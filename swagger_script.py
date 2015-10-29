import argparse
import yaml


def process_method(method_contents):
    aws_contents = method_contents.get('x-amazon-apigateway-integration')
    if aws_contents is None:
        # This method is not associated with a Lambda handler. Don't make any changes.
        return

    responses = method_contents.get('responses')
    if responses is None:
        responses = {}
        method_contents['responses'] = responses

    integration_responses = aws_contents.get('responses')
    if integration_responses is None:
        integration_responses = {}
        aws_contents['responses'] = integration_responses

    add_success_response(responses, integration_responses)
    add_internal_error_response(responses, integration_responses)
    error_status_codes = ['400', '404', '409', '500']
    for status_code in error_status_codes:
        add_error_response(responses, integration_responses, status_code)


def add_success_response(responses, integration_responses):
    if '200' not in responses:
        responses['200'] = {}
    if 'default' not in integration_responses:
        integration_response = {'statusCode': '200'}
        integration_responses['default'] = integration_response


def add_internal_error_response(responses, integration_responses):
    if '500' not in responses:
        responses['500'] = {}
    if '.+' not in integration_responses:
        integration_response = {'statusCode': '500'}
        response_template_contents = """
            {
              "response": {
                "statusCode": 500,
                "faultId": "common.error.general",
                "message": "General error"
              }
            }
        """
        response_template = {'application/json': response_template_contents}
        integration_response['responseTemplates'] = response_template
        integration_responses['.+'] = integration_response


def add_error_response(responses, integration_responses, status_code):
    if status_code not in responses:
        responses[status_code] = {}
    response_regex = '.*"statusCode"\s*:\s*' + status_code + '.*'
    if response_regex not in integration_responses:
        integration_response = {'statusCode': status_code}
        response_template_contents = """
            {
              "response": $input.path('$.errorMessage')
            }
        """
        response_template = {'application/json': response_template_contents}
        integration_response['responseTemplates'] = response_template
        integration_responses[response_regex] = integration_response


def process_file(source_file_path, destination_file_path):
    source_file = file(source_file_path, 'r')
    yaml_contents = yaml.load(source_file)

    for path_name, path_contents in yaml_contents['paths'].iteritems():
        for method_name, method_contents in path_contents.iteritems():
            process_method(method_contents)

    destination_file = file(destination_file_path, 'w')
    yaml.dump(yaml_contents, destination_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_file_path")
    parser.add_argument("destination_file_path")
    args = parser.parse_args()

    # source_file = file('/Users/marek/git/aws-apigateway-importer/swagger-marek.yaml', 'r')
    # source_file = file('/Users/marek/git/BackOfficeAssoc-github/dspcloud/services/dspgovern/api/swagger/service.yaml', 'r')
    # destination_file = file('/Users/marek/git/aws-apigateway-importer/swagger-marek-generated.yaml', 'w')
    # destination_file = file('/Users/marek/git/BackOfficeAssoc-github/dspcloud/services/dspgovern/api/swagger/service-generated.yaml', 'w')

    process_file(args.source_file_path, args.destination_file_path)


#if __name__ == '__main__':
#    main()

process_file(‘swagger-marek.yaml’,’swagger-tranform.yaml’)
