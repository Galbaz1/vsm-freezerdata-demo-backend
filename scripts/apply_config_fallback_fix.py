#!/usr/bin/env python3
"""
Apply config fallback fix to elysia/api/routes/init.py

This modifies the get_default_config() function to:
1. First try: default=True AND user_id=<specific_user>
2. If none found, fallback: default=True AND user_id="default_user"

This allows the VSM config seeded for "default_user" to be used by ALL users
when they don't have their own user-specific config.
"""
import re

init_py_path = "/Users/faustoalbers/vsm-freezerdata-demo-backend/elysia/api/routes/init.py"

print("🔧 Applying Config Fallback Fix")
print("=" * 60)
print(f"Target file: {init_py_path}")

# Read the file
with open(init_py_path, "r") as f:
    content = f.read()

# Find the get_default_config function
function_pattern = r'(async def get_default_config\(.*?\n)(.*?)(if len\(default_configs\.objects\) > 0:)'

# Replacement that adds fallback logic
replacement = r'''\1\2# Fallback to global default_user config if user-specific not found
        if len(default_configs.objects) == 0:
            default_configs = await collection.query.fetch_objects(
                filters=Filter.all_of(
                    [
                        Filter.by_property("default").equal(True),
                        Filter.by_property("user_id").equal("default_user"),
                    ]
                )
            )

        \3'''

# Check if already applied
if 'Fallback to global default_user config' in content:
    print("\n⏭️  Fix already applied! No changes needed.")
else:
    # Apply the fix
    new_content = re.sub(function_pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        # Backup original
        backup_path = init_py_path + ".backup"
        with open(backup_path, "w") as f:
            f.write(content)
        print(f"\n💾 Backup created: {backup_path}")
        
        # Write modified version
        with open(init_py_path, "w") as f:
            f.write(new_content)
        
        print(f"✅ Fix applied successfully!")
        print("\nChanges made:")
        print("  - Added fallback to 'default_user' config when user-specific config not found")
        print("  - This allows VSM config to be shared across all users")
        
        print("\n🔄 Next steps:")
        print("   1. Review the changes: diff elysia/api/routes/init.py elysia/api/routes/init.py.backup")
        print("   2. Run cleanup script: python3 scripts/cleanup_configs.py")
        print("   3. Restart Elysia: elysia start")
        print("   4. Test in browser")
    else:
        print("\n❌ Failed to apply fix - pattern not found in file")
        print("   You may need to apply the fix manually")

print("=" * 60)
