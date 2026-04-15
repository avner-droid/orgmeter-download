from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_csv():
    data = request.json
    mandrill_url = data.get('url')
    password = data.get('password')

    if not mandrill_url or not password:
        return {'error': 'Missing url or password'}, 400

    try:
        session = requests.Session()

        # Step 1: Follow the Mandrill tracking link to get the real OrgMeter URL
        resp = session.get(mandrill_url, allow_redirects=True)

        # The final URL should be like:
        # https://app.orgmeter.com/download/file/{hash}
        final_url = resp.url
        
        # Extract the hash from the URL
        if '/download/file/' in final_url:
            file_hash = final_url.split('/download/file/')[-1].split('?')[0].split('#')[0]
        else:
            return {'error': f'Unexpected URL after redirect: {final_url}'}, 400

        # Step 2: POST the password to the auth endpoint
        auth_url = f'https://app.orgmeter.com/download/auth/{file_hash}/download'
        
        form_data = {
            'secure_url_password[password]': password,
            'secure_url_password[type]': 'asset',
            'secure_url_password[username]': file_hash
        }

        download_resp = session.post(auth_url, data=form_data, allow_redirects=True)

        if download_resp.status_code != 200:
            return {
                'error': f'Download failed with status {download_resp.status_code}',
                'body': download_resp.text[:500]
            }, 400

        # Step 3: Return the CSV content
        return Response(
            download_resp.content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=report.csv'}
        )

    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
