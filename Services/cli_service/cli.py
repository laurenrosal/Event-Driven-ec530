import argparse

def upload(image_path: str):
    #publishes an image.submitted event to the message broker.
    print(f"[CLI] Uploading image: {image_path}")
    # TODO: connect the broker and pushlish image.submitted event


def search(description: str):
    # pulished a query.submitted event to the message broker
    print(f"[CLI] searching for: {description}")
    # TODO: connect to broker and publish query.submitted event


def main():
    parser = argparse.ArgumentParser(prog="cli")
    subparsers = parser.add_subparsers(dest="command")


    upload_parser = subparsers.add_parser(upload)
    upload_parser.add_argument("image_path")


    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("description")

    args = parser.parse_args()

    if args.command == "upload":
        upload(args.image_path)
    elif args.command == search:
        search(args.description)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
