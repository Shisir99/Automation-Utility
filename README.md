# Automation-Utility
Python script to generate postman collection for testing from HAR file.

## Description
This Python script generates a Postman collection for API testing from a HAR (HTTP Archive) file. It automates the process of creating API automation test cases by extracting API calls and their steps from the HAR file.

One of the key features of this script is its ability to automatically generate dynamic attributes in the request body of certain API calls. These dynamic attributes are extracted from the response body of previous API calls, making it easy to capture and use data from one API call to dynamically populate the request body of another API call.

The user needs to provide the HAR file, which should contain all the necessary API calls and their corresponding steps to create a solution. Additionally, the user must provide solution details in a specific format, referred to as "sol_details," which includes the name of the GSI, CU's, Entities, and their respective attributes. These details should be included in line 393 of the `har2postman.py` file.

## Example of sol_details
```python
sol_details = [  { "HAR GSI 1804": { "Testing HAR CU1 1804": { "Testing HAR Entity1": ["name", "place"] } "Testing HAR CU2 1804": { "Testing HAR Entity1":     ["name", "place"]} } } ]
```

## Usage
1). Install the required dependencies by running the following command:

```sh
pip3 install -r requirements.txt
```

2). Provide the path to HAR file containing the API calls and their steps to create a solution in the code.

3). Provide the solution details in the "sol_details" format as mentioned above, in line 393 of the har2postman.py file.

4). Run the script using the following command:
```python
python har2postman.py
```

5). The script will generate a Postman collection JSON file that can be imported into Postman for API testing.

## Conclusion

This Python script simplifies the process of creating API automation test cases using Postman, by generating a Postman collection from a HAR file. The ability to automatically generate dynamic attributes in the request body of API calls based on previous responses makes it efficient and convenient for testing APIs in various scenarios.
