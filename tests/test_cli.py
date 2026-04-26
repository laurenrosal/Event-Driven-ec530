from Services.cli_service.cli import upload_image, search_images

def test_upload_runs():
    upload_image("images/test.jpg")

def test_search_runs():
    search_images("a cat wearing a hat")