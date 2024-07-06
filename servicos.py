import win32serviceutil
import win32service
import win32event
import subprocess
import time
import psutil
import logging
import os
import threading


class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CheckAndStartAppService"
    _svc_display_name_ = "Check and Start App Service"
    _svc_description_ = "This service checks if 'verificar_dash' is running and starts it if not."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.stop_requested = False

        # Setup logging
        log_path = os.path.join(os.path.dirname(__file__), 'check_and_start_app_service.log')
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s'
        )
        logging.info('Service __init__ called.')

    def SvcStop(self):
        self.stop_requested = True
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        logging.info('Service is stopping.')

    def SvcDoRun(self):
        logging.info('Service SvcDoRun called.')
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()

    def main(self):
        # Start the main logic in a separate thread to avoid blocking the service startup
        main_thread = threading.Thread(target=self.run)
        main_thread.start()

        # Keep the service running
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

    def run(self):
        app_name = "verificar_dash.exe"
        app_path = r"C:\Users\joao.silveira\Desktop\Projetos_Programas\projeto_etl\Verificar_DashBoard\dist\verificar_dash\verificar_dash.exe"
        logging.info('Service main loop started.')
        while not self.stop_requested:
            if not self.is_process_running(app_name):
                self.start_app(app_path)
            else:
                logging.info(f'{app_name} is already running.')
            for _ in range(300):  # Check every 5 minutes (300 seconds)
                if self.stop_requested:
                    break
                time.sleep(1)
        logging.info('Service main loop exited.')

    def is_process_running(self, process_name):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.name().lower() == process_name.lower():
                    logging.info(f'Process {process_name} is running.')
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        logging.info(f'Process {process_name} is not running.')
        return False

    def start_app(self, app_path):
        logging.info(f'Starting {app_path}.')
        subprocess.Popen(app_path)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(MyService)
