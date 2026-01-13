BUILD_DIR = "build"

if __name__ == "__main__":
    from contracts.example_contracts import compile_all
    compile_all(BUILD_DIR)