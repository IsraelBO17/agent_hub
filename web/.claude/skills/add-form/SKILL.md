---
name: add-form
description: "Add a form with a zod schema, the shared field kit, a pending state and server field errors mapped onto fields. Use when users need to enter or edit data."
argument-hint: "[form and the operation it submits to]"
---

Add a form by following **recipe 7** in `docs/RECIPES.md` exactly. The form: $ARGUMENTS

1. Read recipe 7 and standard §13. Check the request schema in the contract.
2. Write the schema in the module's `schemas.ts` and the form, copying `note-form.tsx`, with fields from `components/form/`.
3. Map `ApiError.fieldErrors` onto fields and focus the first; toast anything else.
4. Test the blocked submit, a server field error and success.
5. Run `make check` and `make e2e`, submit it by keyboard only, and report.
