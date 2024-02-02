## Invoking a WASM function

To invoke a function execution in Faasm, you first need to [upload](upload.md)
it.

Then, you may use the same `(user, function)` pair used to upload the function
to invoke it:

```bash
faasmctl invoke <user> <func>
```
