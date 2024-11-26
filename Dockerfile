FROM python:3.11.9-slim-bullseye
WORKDIR /workdir
COPY . .
RUN pip3 install -r /workdir/requirements.txt

ENTRYPOINT ["python3", "/workdir/update_vm_registry.py"]