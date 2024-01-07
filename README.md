# AppSync GraphQL API with Lambda

This repository contains the code for creating an AppSync GraphQL API with Lambda with the espn hidden API. The API allows you to build scalable and flexible serverless applications with GraphQL as the query language.

## Prerequisites

Before getting started, make sure you have the following prerequisites installed:

- [AWS CLI](https://aws.amazon.com/cli/)
- [Python3.8+]

## Getting Started

1. Clone this repository or create your own:

    ```bash
    git clone https://github.com/your-username/your-repo.git
    ```

2. Install the dependencies and create a zip file:

    ```bash
    cd lambda/schedule
    mkdir package
    pip3 install -r requirements.txt --target ./package
    cd package
    zip -r ../my_deployment_package.zip .
    cd ..
    zip my_deployment_package.zip lambda_function.py

    cd lambda/odds
    mkdir package
    pip3 install -r requirements.txt --target ./package
    cd package
    zip -r ../my_deployment_package.zip .
    cd ..
    zip my_deployment_package.zip lambda_function.py
    ```

3. Configure your AWS credentials:

    ```bash
    aws configure
    ```


4. Deploy the Lambda functions:

    ```bash
    cd lambda/schedule
    aws lambda create-function --function-name scheduleAPI \
    --runtime python3.11 --handler lambda_function.lambda_handler \
    --role <Add lambda role> \
    --zip-file fileb://my_deployment_package.zip \
    --profile <your profile>

    cd lambda/odds
    aws lambda create-function --function-name oddsAPI \
    --runtime python3.11 --handler lambda_function.lambda_handler \
    --role <Add lambda role> \
    --zip-file fileb://my_deployment_package.zip \
    --profile <your profile>
    ```

5. Create AppSync API in lambda console and use lambda as resolver for scheduleData query and odds for the gameData query. GraphQL schema is located in the appsync folder.

6. Once the deployment is complete, you will see the API endpoint URL. Use this URL to interact with your GraphQL API.

## Usage

To use the AppSync GraphQL API, you can use tools like [GraphQL Playground](https://www.graphqlbin.com/v2/new) or [Postman](https://www.postman.com/).

1. Open your preferred GraphQL client.

2. Set the endpoint URL to the API endpoint URL obtained during deployment.

3. Start sending GraphQL queries and mutations to interact with your API.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
