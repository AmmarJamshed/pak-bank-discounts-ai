import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
import shutil


def run_command(command, cwd=None, wait=True, capture=False, timeout=None):
    if wait:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return result
    return subprocess.Popen(command, cwd=cwd)


def run_command_stream(command, cwd=None, log_path=None):
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.stdout:
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(line)
                if log_path:
                    write_log(log_path, line)
    return process.wait()


def write_log(path, content):
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(content + "\n")
    except Exception:
        pass


def run_command_checked(command, cwd=None, log_path=None, timeout=None, error_message=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        missing = f"Command not found: {command[0]}"
        print(missing)
        write_log(log_path, missing)
        sys.exit(1)

    if result.stdout:
        write_log(log_path, result.stdout.rstrip())
    if result.stderr:
        write_log(log_path, result.stderr.rstrip())

    if result.returncode != 0:
        print(error_message or f"Command failed: {' '.join(command)}")
        print(f"Details written to {log_path}")
        sys.exit(1)

    return result


def start_command(command, cwd=None, log_path=None):
    try:
        if log_path:
            log_handle = open(log_path, "a", encoding="utf-8")
            return subprocess.Popen(
                command,
                cwd=cwd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        return subprocess.Popen(command, cwd=cwd)
    except FileNotFoundError:
        missing = f"Command not found: {command[0]}"
        print(missing)
        write_log(log_path, missing)
        sys.exit(1)


def wait_for_url(url, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(2)
    return False


def _get_root_dir() -> str:
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(exe_dir, ".."))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    root_dir = _get_root_dir()
    frontend_dir = os.path.join(root_dir, "frontend")
    frontend_port = int(os.environ.get("FRONTEND_PORT", "3000"))
    frontend_url = f"http://localhost:{frontend_port}"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"

    log_path = os.path.join(root_dir, "launcher.log")

    print("Checking Docker...")
    docker_path = shutil.which("docker")
    write_log(log_path, f"Docker path: {docker_path or 'NOT FOUND'}")
    try:
        docker_check = run_command(
            ["docker", "version"], cwd=root_dir, capture=True, timeout=20
        )
    except subprocess.TimeoutExpired:
        print("Docker command timed out. Please restart Docker Desktop.")
        write_log(log_path, "Docker version command timed out.")
        sys.exit(1)
    if docker_check.returncode != 0:
        write_log(log_path, docker_check.stdout or "")
        write_log(log_path, docker_check.stderr or "")
        print("Docker is not available. Install Docker Desktop and start it.")
        print(f"Details written to {log_path}")
        sys.exit(1)

    print("Starting Docker services (first run may take several minutes)...")
    compose_file = os.path.join(root_dir, "docker-compose.yml")
    compose_exit = run_command_stream(
        ["docker", "compose", "-f", compose_file, "up", "--build", "-d"],
        cwd=root_dir,
        log_path=log_path,
    )
    if compose_exit != 0:
        print("Docker compose failed. See launcher.log for details.")
        print(f"Log: {log_path}")
        sys.exit(1)

    print("Ensuring frontend dependencies...")
    npm_path = shutil.which(npm_cmd)
    write_log(log_path, f"NPM path: {npm_path or 'NOT FOUND'}")
    if not npm_path:
        print("npm is not available. Install Node.js (includes npm).")
        print(f"Details written to {log_path}")
        sys.exit(1)

    node_modules = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules):
        print("Installing frontend dependencies...")
        run_command_checked(
            [npm_cmd, "install"],
            cwd=frontend_dir,
            log_path=log_path,
            error_message="npm install failed. Ensure Node.js is installed.",
        )

    next_build_id = os.path.join(frontend_dir, ".next", "BUILD_ID")
    if not os.path.exists(next_build_id):
        print("Building frontend...")
        run_command_checked(
            [npm_cmd, "run", "build"],
            cwd=frontend_dir,
            log_path=log_path,
            error_message="Frontend build failed.",
        )

    print(f"Starting frontend on port {frontend_port}...")
    frontend_process = start_command(
        [npm_cmd, "run", "start", "--", "-p", str(frontend_port)],
        cwd=frontend_dir,
        log_path=log_path,
    )

    print("Waiting for backend and frontend...")
    if not wait_for_url("http://localhost:8000/health", timeout=180):
        print("Backend did not become ready.")
        frontend_process.terminate()
        sys.exit(1)

    if not wait_for_url(frontend_url, timeout=180):
        print("Frontend did not become ready.")
        frontend_process.terminate()
        sys.exit(1)

    print("Opening browser...")
    webbrowser.open(frontend_url)

    try:
        frontend_process.wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
