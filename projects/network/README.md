# CyberSutech — HTTP vs HTTPS Security Lab

CyberSutech HTTP vs HTTPS Security Lab is a lightweight educational web application developed for the Networking section of CyberSutech Magazine.

The project is designed to demonstrate the fundamental differences between HTTP and HTTPS through a simple web application with Login and Registration functionality. It provides a controlled local environment where network traffic can be captured and analyzed using Wireshark.

## Purpose

The main purpose of this project is to provide a practical environment for demonstrating:

- The difference between HTTP and HTTPS
- How HTTP requests are transmitted without encryption
- How HTTPS protects application data using TLS
- HTTP POST requests and form data
- TLS encrypted application data
- Network packet capture and analysis using Wireshark
- The role of encryption in protecting sensitive information

This project is intended for educational, research, and local laboratory use only.

## Features

- Simple and responsive user interface
- CyberSutech branding
- University and magazine logos
- Login page
- Registration page
- Dashboard page
- SQLite database
- Password hashing
- Session-based authentication
- HTTP server
- HTTPS server
- Self-signed TLS certificate
- Wireshark-compatible network traffic
- Separate HTTP and HTTPS ports for easy comparison

## Available Services

The application runs on two different ports:

| Protocol | URL | Port |
|----------|-----|------|
| HTTP | http://127.0.0.1:8000 | 8000 |
| HTTPS | https://127.0.0.1:8443 | 8443 |

Both services provide the same application, allowing HTTP and HTTPS traffic to be compared directly.

## Project Structure

cybersutech-wireshark-lab/

├── server.py  
├── index.html  
├── login.html  
├── register.html  
├── dashboard.html  
├── style.css  
├── README.md  
├── .gitignore  
│  
└── assets/  
    ├── cybersutech-logo.png  
    └── university-logo.jpeg

TLS certificates and local database files should not be committed to the repository.

## Requirements

The project requires:

- Python 3.9 or newer
- Wireshark
- Npcap on Windows

The server uses Python's built-in modules and does not require a web framework for the basic setup.

## Running the Project

Clone the repository:

git clone <repository-url>

Navigate to the project directory:

cd network/cybersutech-wireshark-lab

Start the server:

python server.py

The HTTP version of the application will be available at:

http://127.0.0.1:8000

The HTTPS version will be available at:

https://127.0.0.1:8443

Because the HTTPS server uses a self-signed certificate, the browser may display a certificate security warning. This is expected in a local educational environment.

## Database

The application uses SQLite to store registered users.

The database is created locally by the application and contains user information such as:

- User ID
- Username
- Email
- Password hash
- Account creation time

Passwords are stored as hashes rather than plaintext values.

The local database file should not be committed to Git.

Recommended entries in `.gitignore` include:

*.db
*.sqlite
*.sqlite3

Private TLS keys and other sensitive files should also be excluded from version control.

## Wireshark Demonstration

The main purpose of this project is to demonstrate the difference between HTTP and HTTPS traffic using Wireshark.

### HTTP

Open the following address:

http://127.0.0.1:8000

Start a Wireshark capture on the Loopback Interface.

A useful Wireshark display filter is:

tcp.port == 8000

Perform a test Login or Registration using a non-sensitive test account.

Because HTTP does not provide transport-layer encryption, HTTP requests and application-level data may be visible in the captured traffic.

For example, a form submission may contain information similar to:

POST /login

username=testuser  
password=Test12345

The exact packet representation depends on the browser, server, and capture configuration.

### HTTPS

Open:

https://127.0.0.1:8443

Start a Wireshark capture on the Loopback Interface.

Use the following display filter:

tcp.port == 8443

Perform the same Login or Registration operation using a test account.

The connection is protected by TLS. Instead of seeing the application data directly, Wireshark will show TLS traffic and encrypted application data.

## HTTP vs HTTPS

The project can be used to demonstrate the following conceptual difference.

HTTP:

Client → HTTP Request → Server

The HTTP request is transmitted without TLS encryption.

HTTPS:

Client → TLS → Encrypted Application Data → Server

The application data is protected by TLS during transmission.

This provides a simple visual and practical demonstration of why HTTPS is preferred when transmitting authentication information and other sensitive data.

## Recommended Demonstration Workflow

For an educational demonstration, the following workflow is recommended:

1. Start the CyberSutech server.
2. Open Wireshark.
3. Select the Loopback Interface.
4. Capture traffic on port 8000.
5. Open the HTTP version of the website.
6. Submit a test Login or Registration form.
7. Inspect the captured HTTP packets.
8. Stop the capture and save it as an HTTP `.pcapng` file.
9. Start a new Wireshark capture.
10. Open the HTTPS version of the website.
11. Submit the same type of test form.
12. Inspect the TLS traffic.
13. Compare the HTTP and HTTPS captures.

This workflow makes it possible to demonstrate how information that may be visible in HTTP becomes encrypted when HTTPS is used.

## Security Notice

This project is designed specifically for local educational and laboratory demonstrations.

It is not intended for production deployment.

The HTTPS configuration uses a self-signed certificate. Self-signed certificates are suitable for local testing and educational environments but are not a replacement for certificates issued by a trusted Certificate Authority in production systems.

Do not use real passwords, personal information, or other sensitive data during packet-capture demonstrations.

Always use test accounts and test data when analyzing traffic with Wireshark.

## CyberSutech Magazine

CyberSutech is a technology magazine covering four main areas:

- Artificial Intelligence
- Software
- Hardware
- Networking

This project belongs to the Networking section and focuses on introducing practical concepts in network security, HTTP, HTTPS, TLS, authentication, and packet analysis.

## Educational Scope

This laboratory is intended to provide a simple practical introduction to network security concepts.

By combining a functional web application with Wireshark packet capture, users can observe the difference between unencrypted HTTP communication and TLS-protected HTTPS communication in a controlled local environment.

## License

This project is provided for educational and research purposes.