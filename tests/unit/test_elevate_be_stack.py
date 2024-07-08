import aws_cdk as core
import aws_cdk.assertions as assertions

from infra.elevate_be_stack import ElevateBeStack


# example tests. To run these tests, uncomment this file along with the example
# resource in elevate_be/elevate_be_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ElevateBeStack(app, "elevate-be")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
