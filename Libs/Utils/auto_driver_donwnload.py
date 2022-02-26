import webdrivermanager


def download_driver():
    """
    To download chrome driver
    :returns chrome driver executable path if downloaded successfully, else None
    """
    # download webdriver zip and unpack
    driver_manager = webdrivermanager.ChromeDriverManager()
    path_tuple = driver_manager.download_and_install(show_progress_bar=False)
    if len(path_tuple) > 1:
        return path_tuple[1]
