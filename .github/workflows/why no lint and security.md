# Why no lint and security?
- Linting and security checks are important for any project.
- But the dependencies in this project can't be installed on the same environment.
- Docker resolved problem, but the tests will fail anyway, so i decided to put the lint and security on the other plan // to be continued

```yml
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install linting dependencies
      run: |
        pip install flake8 black mypy

    - name: Run linters
      run: |
        flake8 src tests
        black --check src tests
        mypy src

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Install security tools
      run: |
        pip install bandit
        go install github.com/securego/gosec/v2/cmd/gosec@latest

    - name: Run Bandit
      run: |
        bandit -r src/

    - name: Run Gosec
      run: |
        gosec ./...
        
