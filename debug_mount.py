import modal.mount
print(f"Has Mount in modal.mount: {'Mount' in dir(modal.mount)}")
try:
    from modal import Mount
    print("Imported Mount from modal")
except ImportError:
    print("Could not import Mount from modal")

try:
    from modal.mount import Mount
    print("Imported Mount from modal.mount")
except ImportError:
    print("Could not import Mount from modal.mount")
