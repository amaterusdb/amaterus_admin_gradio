from argparse import ArgumentParser, Namespace


def main():
    parser = ArgumentParser()
    args = parser.parse_args()

    print(args)


if __name__ == "__main__":
    main()
