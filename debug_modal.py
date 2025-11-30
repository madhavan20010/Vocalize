import modal
print(f"Modal Version: {getattr(modal, '__version__', 'unknown')}")
print(f"Has Mount: {'Mount' in dir(modal)}")
print(dir(modal))
