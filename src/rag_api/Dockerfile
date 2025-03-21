# Define custom function directory
ARG FUNCTION_DIR="/var/task"

FROM python:3.12 AS build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy requirements.txt
RUN mkdir -p ${FUNCTION_DIR}
COPY requirements.txt ${FUNCTION_DIR}
RUN pip install -r ${FUNCTION_DIR}/requirements.txt --target ${FUNCTION_DIR}
RUN pip install \
    --target ${FUNCTION_DIR} \
        awslambdaric

# Copy function code
COPY . ${FUNCTION_DIR}

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.12-slim

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]

# Pass the name of the function handler as an argument to the runtime
CMD [ "index.handler" ]
