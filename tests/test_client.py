import unittest
from unittest.mock import Mock, patch

from codex_usage.client import CodexClientError, read_usage


def failure(message):
    return {"error": {"message": message}}


class AuthenticationRecoveryTests(unittest.TestCase):
    def run_client(self, responses):
        process = Mock()
        with patch('codex_usage.client.find_codex', return_value='/bin/codex'), \
             patch('codex_usage.client.subprocess.Popen', return_value=process), \
             patch('codex_usage.client._wait_for_response', side_effect=responses), \
             patch('codex_usage.client._send') as send:
            try:
                result = read_usage()
            finally:
                self.sent = [call.args[1] for call in send.call_args_list]
                process.terminate.assert_called_once()
        return result

    def test_success_does_not_refresh_tokens(self):
        self.assertEqual(self.run_client([{'result': {}}, {'result': {}}]), [])
        self.assertNotIn('account/read', [m['method'] for m in self.sent])

    def test_revoked_token_refreshes_then_retries(self):
        self.assertEqual(self.run_client([
            {'result': {}}, failure('401 Unauthorized: token_revoked'),
            {'result': {'account': {'type': 'chatgpt'}}}, {'result': {}},
        ]), [])
        self.assertEqual(self.sent[-2], {
            'method': 'account/read', 'id': 2, 'params': {'refreshToken': True}})
        self.assertEqual(self.sent[-1]['id'], 3)

    def test_failed_refresh_explains_login(self):
        with self.assertRaisesRegex(CodexClientError, 'codex login'):
            self.run_client([{'result': {}}, failure('token_revoked'),
                             failure('refresh_token_reused')])
        self.assertEqual(self.sent[-1]['method'], 'account/read')

    def test_retry_is_bounded(self):
        with self.assertRaisesRegex(CodexClientError, 'codex login'):
            self.run_client([{'result': {}}, failure('401 Unauthorized'),
                             {'result': {}}, failure('token_revoked')])
        self.assertEqual(len(self.sent), 5)

    def test_network_error_is_not_treated_as_authentication(self):
        with self.assertRaisesRegex(CodexClientError, 'connection refused'):
            self.run_client([{'result': {}}, failure('connection refused')])
        self.assertEqual(len(self.sent), 3)
