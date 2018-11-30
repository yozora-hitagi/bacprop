FROM python:3.6.6-alpine3.8
RUN pip3 install pipenv

WORKDIR /bacprop

COPY Pipfile.lock Pipfile ./

RUN pipenv install --system --deploy --ignore-pipfile

COPY bacprop bacprop

ENTRYPOINT [ "python", "/bacprop/run.py" ]
