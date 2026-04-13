from Services.cli_service.cli import upload, search

def test_upload_runs():
    upload("images/test.jpg")

def test_search_runs():
    search("a cat wearing a hat")