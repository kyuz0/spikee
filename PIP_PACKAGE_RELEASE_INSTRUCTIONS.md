# Release Workflow

At some point this needs to be part of a pipeline.

1. **Install tools**  
   ```bash
   python -m pip install --upgrade build wheel twine
   ```

2. **Build**  
   ```bash
   python -m build
   ```

3. **(Optional) Test-upload**  
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple spikee
   ```

4. **Publish**  
   ```bash
   twine upload dist/*
   ```

5. **Bump & tag**  
   ```bash
   # edit pyproject.toml → version
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```
