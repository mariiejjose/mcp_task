# MCP HelpDesk Assistant

The goal was to build a command-line IT HelpDesk Assistant that connects an AI model to an MCP server. The assistant can search common IT FAQs, create and manage support tickets, remember previous messages in the conversation, and use MCP tools automatically when needed.

I used Gemini 2.5 Flash through OpenRouter because this was the API setup provided to me during the internship.

## What the project does

The chatbot can:
- Search the IT FAQ before creating a ticket
- Create new support tickets
- Get the details of a ticket
- List tickets
- Show tickets belonging to a specific employee
- Close tickets with a resolution
- Remember previous messages during the same conversation
- Handle multiple MCP tool calls in one user request
- Ask for confirmation before actions that change data
- Handle MCP tool errors without crashing
- Handle API errors and rate limits
(STRETCH GOALS)
- Use the `/triage` MCP prompt
- Store tickets permanently using SQLite
- Connect to the MCP server using Streamable HTTP
- Use MCP elicitation so the server can ask for confirmation before closing a ticket

## Project files

### helpdesk_server.py
This is the MCP server.
It contains the helpdesk tools, resources, prompts, SQLite database logic, and server-side elicitation.

### chatbot.py
This is the MCP client and chatbot.
It connects to the helpdesk server, discovers the available tools and prompts, sends them to Gemini, handles tool calls, keeps conversation history, and prints the final answers.

### test_helpdesk.py
Contains the pytest tests for the MCP server.

### helpdesk.db
SQLite database used to store the support tickets so they are not lost when the program restarts.

### requirements.txt
Contains the Python dependencies needed to run the project.

### .env
Contains the API key.
This file is not committed to GitHub because it is included in `.gitignore`.

## MCP tools
The server provides these tools:
`search_faq`: Searches the IT FAQ for common problems 
`create_ticket`: Creates a new support ticket 
`get_ticket`: Gets the details and status of one ticket 
`list_tickets`: Lists all tickets or filters them by status 
`my_tickets`: Lists the tickets belonging to one employee 
`close_ticket`: Closes a ticket and stores the resolution 

The read-only tools use the MCP `read_only_hint` annotation.
`close_ticket` uses the `destructive_hint` annotation because it changes ticket data.

## MCP resource
The server provides a dynamic ticket resource: helpdesk://tickets/{ticket_id}
It returns the information stored for ticket x.

## MCP prompt
The server provides an MCP prompt called: triage
The prompt is used to help handle a new IT problem.
The user can call it from the chatbot using:
/triage my laptop is slow
The chatbot detects the `/triage` command, gets the `triage` prompt from the MCP server, and sends the returned instructions to the AI model.
The triage prompt tells the assistant to check the FAQ first and then suggest creating a support ticket if the FAQ does not solve the problem.

## System prompt
I added a system prompt to make the chatbot behave like an IT helpdesk assistant.
The main rules are:
- Check the FAQ before suggesting a new ticket
- Use the MCP tools instead of inventing ticket information
- Use previous conversation history for follow-up questions
- Do not ask the user to repeat information that is already available in the conversation
For example:
Q: What tickets does Omar have?
A: Omar has ticket #1002.
Q: Close the first one.

The chatbot can understand that "the first one" refers to ticket 1002 because the conversation history is kept during the session.

## Tool-use loop
The chatbot uses a tool-use loop.
The basic flow is:
1- User sends a message
2- Gemini receives the message and available tools
3- Gemini decides whether a tool is needed
4- The MCP client calls the requested tool
5- The MCP server executes the tool
6- The tool result is sent back to Gemini
7- Gemini creates the final answer

The chatbot can also handle several tool calls in the same turn.
A maximum number of tool rounds is used so the model cannot continue calling tools forever.

## Conversation history
The chatbot keeps the conversation history for the whole session.
This allows follow-up questions to work.
Example:
Q: What is the status of ticket 1002?
A: Ticket 1002 is currently in progress.
Q: Who owns it?
A: Omar owns ticket 1002.

The second question does not include the ticket number, but the chatbot understands what "it" refers to because the previous conversation is still available.

## Safety and confirmation
Actions that change data require confirmation.

### Creating a ticket
Before `create_ticket` is executed, the chatbot asks the user for confirmation.
If the user says no, the tool is not executed.

### Closing a ticket
For `close_ticket`, I implemented server-side confirmation using MCP elicitation.
This means the MCP server itself asks the user for confirmation before changing the ticket.
Example:
Server asks: Are you sure you want to close ticket #1001?
Confirm? (y/n):

If the user says no, the ticket is not closed.

## Error handling
The chatbot handles MCP tool errors without crashing.
For example, if the user asks for a ticket that does not exist:
Q: What is the status of ticket 90?

the tool returns an error and the chatbot explains the problem instead of stopping the program.
The chatbot also handles:
- MCP tool errors
- API connection errors
- Rate-limit errors
- Maximum tool rounds

If the AI service is unavailable, the chatbot returns a friendly message instead of showing a traceback.

## SQLite storage
Originally, the tickets were stored inside a Python dictionary.
As one of the stretch goals, I changed the project to use SQLite.
The database file is:helpdesk.db
The `tickets` table contains:
id
title
priority
status
owner
created
resolution

The MCP tools now read and write directly to SQLite.
This means tickets are still available after the server is stopped and restarted.

## Streamable HTTP
The original project used stdio to connect the MCP client and server.
As one of the stretch goals, I changed the server to use Streamable HTTP.
The MCP server runs at: http://127.0.0.1:8000/mcp
This means the server and chatbot run as separate processes.

## Slash commands
I added support for the MCP `triage` prompt through a slash command.
Example:
/triage my laptop is slow

The chatbot detects the command and calls the MCP prompt called `triage`.
This allows the user to directly select an MCP prompt instead of only sending a normal message.

## Stretch goals completed
I completed four stretch goals.

### 1. Slash commands
The chatbot discovers the MCP prompts and supports:
/triage my laptop is slow

### 2. SQLite storage
Tickets are stored in SQLite so they survive server restarts.

### 3. Streamable HTTP
The chatbot connects to the MCP server using an HTTP URL instead of stdio.

### 4. Server-side confirmation
The `close_ticket` tool uses MCP elicitation so the server itself asks for confirmation before closing a ticket.

## Running the project

Because the project uses Streamable HTTP, the MCP server and chatbot need to run in two separate terminals.

### Terminal 1 - Start the MCP server
Activate the virtual environment and run: python helpdesk_server.py
Leave this terminal running.
The MCP server will be available at: http://127.0.0.1:8000/mcp

### Terminal 2 - Start the chatbot
Open another terminal and activate the virtual environment: .venv\Scripts\activate
Then run: python chatbot.py
When the chatbot starts, it prints the tools it discovered from the MCP server and the discovered prompts.

## Model and API

The chatbot uses: google/gemini-2.5-flash
through OpenRouter.
The OpenRouter API key is loaded from the `.env` file using `python-dotenv`.
The API key is never hardcoded inside the Python files.


## What I learned

Before this project, I understood the basic idea of MCP, but I did not fully understand how the server, client, model, tools, resources, and prompts all worked togther.
Building the project helped me understand that the AI model does not directly execute the MCP tools. The model only requests a tool call. The MCP client receives that request, calls the tool on the MCP server, gets the result, and sends it back to the model.
I also learned the difference between tools, resources, and prompts, how conversation history works, how to handle tool errors, how confirmations should work for destructive actions, and how MCP can use both stdio and Streamable HTTP.
The stretch goals helped me understand how MCP can be used in a more realistic project instead of only using simple in-memory examples.

## License
This project is released under the MIT License.