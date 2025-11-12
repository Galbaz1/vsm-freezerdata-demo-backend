# Cursor Configuration

This directory contains project-level Cursor configuration for AI-assisted development.

## 📂 Directory Structure

```
.cursor/
├── rules/                      # Project rules (version-controlled)
│   ├── always/                # Always applied rules
│   ├── agent-requested/       # Rules agent can choose to include
│   ├── auto-attached/         # Path-scoped rules (auto-attach via globs)
│   └── manual/                # Explicitly referenced rules (@ruleName)
├── commands/                   # Custom slash commands
├── hooks.json                  # Hook configuration (beta)
└── README.md                   # This file
```

## 📋 Rules

Rules provide persistent context and instructions to Cursor Agent and Inline Edit. They ensure consistent behavior across coding sessions.

### Rule Types

#### **Always Applied** (`always/`)
Core principles applied to every Agent interaction.

- **`slicing.mdc`** - Vertical slicing architecture principles
  - Enforces feature-centric organization (UI → domain → data)
  - Maintains slice boundaries and import rules

#### **Agent Requested** (`agent-requested/`)
Contextual rules the agent can choose to include based on relevance.

- **`codebase-naming-conventions.mdc`** - File and directory naming standards
  - Applied when creating or naming new files
  - Ensures consistency across codebase

- **`features-slice-template.mdc`** - Feature slice scaffolding
  - Used when editing/creating files in `features/{slice}/`
  - Enforces slice boundaries and composition patterns

- **`shared-template.mdc`** - Shared module guidelines
  - Applied when working with `shared/` directory
  - Prevents domain coupling in shared code

- **`rule-creation-guidelines.mdc`** - Meta-rule for creating new rules
  - Guides rule authoring and organization
  - Defines rule types and best practices

- **`docs-navigation-guide.mdc`** - RAG and Context Engineering docs reference
  - Quick navigation for docs/rag/ and docs/context_engineering/
  - Decision tree for finding relevant documentation

#### **Auto-Attached** (`auto-attached/`)
Rules automatically included when specific file patterns are referenced.

- Currently empty - add rules with `globs` metadata to auto-attach based on file paths

#### **Manual** (`manual/`)
Framework-specific and specialized rules referenced explicitly with `@ruleName`.

- **`chrome-extension-development.mdc`**
- **`expo-react-native-typescript-cursor-rules.mdc`**
- **`fastapi-python-cursor-rules.mdc`**
- **`modern-web-development-react.mdc`**
- **`modern-web-development.mdc`**
- **`viewcomfy-API-rules.mdc`**

### Nested Rules

Subdirectories can have their own `.cursor/rules/` directories:

- **`presentation/.cursor/rules/`** - Presentation-specific rules
  - `typography-design-system.mdc` - Typography and design system standards

## 🪝 Hooks (Beta)

Hooks observe and control the Agent loop using custom scripts. Defined in `hooks.json`.

### Current Hooks

#### `afterFileEdit`
Triggered after the Agent edits a file.

1. **Slice Boundary Check**
   ```bash
   pnpm run check:slices
   ```
   Enforces vertical-slice boundaries and import rules.

2. **Naming Convention Check**
   ```bash
   pnpm run check:naming
   ```
   Validates file naming conventions.

#### `stop`
Triggered when the Agent session ends.

1. **Affected Tests**
   ```bash
   pnpm run test:affected-slices
   ```
   Runs tests for slices modified during the session.

### Hook Scripts

All hook scripts are defined in `presentation/package.json`:

```json
{
  "check:slices": "node ./scripts/check-slices.mjs",
  "check:naming": "node ./scripts/check-naming.mjs",
  "test:affected-slices": "node ./scripts/test-affected-slices.mjs"
}
```

Scripts located in `/scripts/`:
- `check-slices.mjs` - Validates slice boundaries
- `check-naming.mjs` - Validates naming conventions
- `test-affected-slices.mjs` - Runs tests for modified slices

### Best Practices

- ✅ Hooks are lightweight and fast
- ✅ Version-controlled for team consistency
- ⚠️ Hooks are beta - tested in safe environments
- ⚠️ Scripts include graceful error handling

## 📝 Creating New Rules

1. **Choose Rule Type**
   - Always: Core principles (use sparingly)
   - Agent-Requested: Contextual guidance
   - Auto-Attached: Path-scoped rules
   - Manual: Specialized/framework-specific

2. **Create File**
   ```bash
   # Via Cursor: Cmd+Shift+P → "New Cursor Rule"
   # Or: Cursor Settings → Rules → Create New Rule
   ```

3. **Add Metadata**
   ```yaml
   ---
   description: "Short description for agent-requested"
   globs:
     - "path/**"           # For auto-attached only
   alwaysApply: false      # true only for always/ rules
   ---
   ```

4. **Write Rule Content**
   - Keep under 500 lines
   - Be specific and actionable
   - Include concrete examples
   - Reference files with `@filename.ts`

5. **Generate from Chat**
   Use `/Generate Cursor Rules` command in Agent chat

## 🔗 References

- [Cursor Rules Documentation](https://docs.cursor.com/en/context/rules)
- [Cursor Hooks Documentation](https://docs.cursor.com/changelog/1-7)
- Project Docs:
  - `/docs/cursor_rules.md` - Detailed rules guide
  - `/docs/hooks.md` - Hooks implementation guide

## 🚀 Quick Tips

- **View Active Rules**: Check Agent sidebar
- **Reference Rule**: Use `@ruleName` in chat
- **Test Hooks**: Make an edit and observe script execution
- **Rule Scope**: Nested rules apply only to their directory

---

**Last Updated:** October 2025  
**Cursor Version:** 1.7+  
**Status:** Production Ready

