from google import genai

API_KEY = 'API_key'

print("started backend.py file!")

def get_file_contents(filename):
    try:
        with open(filename, 'r') as f:
            # It's assumed our file contains a single line,
            # with our API key
            return f.read().strip()
    except FileNotFoundError:
        print("'%s' file not found" % filename)

print("created get_file_contents function")

api_key = get_file_contents(API_KEY)

print("Your API_key is: ", api_key)

client = genai.Client(apikey = api_key)
response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works"
)
print(response.text)