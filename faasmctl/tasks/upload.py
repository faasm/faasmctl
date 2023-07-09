from faasmctl.util.upload import upload_wasm
from invoke import task


@task
def wasm(ctx, user, func, wasm_file, ini_file=None):
    """
    Upload a WASM file under user/func (from --wasm-file)
    """
    # Directly call the util function so that it uses the same code than the
    # API consumers (i.e. using faasmctl in a python script)
    upload_wasm(user, func, wasm_file, ini_file)
