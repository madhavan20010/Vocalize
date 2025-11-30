import modal
import modal.mount

print("modal.mount attributes:")
print(dir(modal.mount))

print("\nmodal attributes:")
print(dir(modal))

# Check if there is a function to create a mount
for attr in dir(modal):
    val = getattr(modal, attr)
    if str(val).find("Mount") != -1:
        print(f"Found Mount-related in modal: {attr} -> {val}")
