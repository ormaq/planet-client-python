"""Tests of the Subscriptions CLI (aka planet-subscriptions)

There are 6 subscriptions commands:

[x] planet subscriptions list
[x] planet subscriptions describe
[x] planet subscriptions results
[x] planet subscriptions create
[x] planet subscriptions update
[x] planet subscriptions cancel

TODO: tests for 3 options of the planet-subscriptions-results command.

"""

import json

from click.testing import CliRunner
import pytest

from planet.cli import cli

from test_subscriptions_api import (api_mock,
                                    failing_api_mock,
                                    create_mock,
                                    update_mock,
                                    cancel_mock,
                                    describe_mock,
                                    res_api_mock,
                                    TEST_URL)

# CliRunner doesn't agree with empty options, so a list of option
# combinations which omit the empty options is best. For example,
# parametrizing 'limit' as '' and then executing
#
# CliRunner().invoke(cli.main, args=['subscriptions', 'list', limit]
#
# does not work.


@pytest.fixture
def invoke():

    def _invoke(extra_args, runner=None, **kwargs):
        runner = runner or CliRunner()
        args = ['subscriptions', f'--base-url={TEST_URL}'] + extra_args
        return runner.invoke(cli.main, args=args, **kwargs)

    return _invoke


@pytest.mark.parametrize('options,expected_count',
                         [(['--status=running'], 100), ([], 100),
                          (['--limit=1', '--status=running'], 1),
                          (['--limit=2', '--pretty', '--status=running'], 2),
                          (['--limit=1', '--status=preparing'], 0)])
@api_mock
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_list_options(invoke, options, expected_count):
    """Prints the expected sequence of subscriptions."""
    # While developing it is handy to have click's command invoker
    # *not* catch exceptions, so we can use the pytest --pdb option.
    result = invoke(['list'] + options, catch_exceptions=False)
    assert result.exit_code == 0  # success.

    # For a start, counting the number of "id" strings in the output
    # tells us how many subscription JSONs were printed, pretty or not.
    assert result.output.count('"id"') == expected_count


@failing_api_mock
def test_subscriptions_create_failure(invoke):
    """An invalid subscription request fails to create a new subscription."""
    # This subscription request lacks the required "delivery" and
    # "source" members.
    sub = {'name': 'lol'}

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', '-'],
        input=json.dumps(sub),
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.
    assert "Error:" in result.output


# This subscription request has the members required by our fake API.
# It must be updated when we begin to test against a more strict
# imitation of the Planet Subscriptions API.
GOOD_SUB_REQUEST = {'name': 'lol', 'delivery': True, 'source': 'wut'}


@pytest.mark.parametrize('cmd_arg, runner_input',
                         [('-', json.dumps(GOOD_SUB_REQUEST)),
                          (json.dumps(GOOD_SUB_REQUEST), None)])
@create_mock
def test_subscriptions_create_success(invoke, cmd_arg, runner_input):
    """Subscriptions creation succeeds with a valid subscription request."""

    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


# Invalid JSON.
BAD_SUB_REQUEST = '{0: "lolwut"}'


@pytest.mark.parametrize('cmd_arg, runner_input', [('-', BAD_SUB_REQUEST),
                                                   (BAD_SUB_REQUEST, None)])
def test_subscriptions_bad_request(invoke, cmd_arg, runner_input):
    """Short circuit and print help message if request is bad."""
    # The "-" argument says "read from stdin" and the input keyword
    # argument specifies what bytes go to the runner's stdin.
    result = invoke(
        ['create', cmd_arg],
        input=runner_input,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 2  # bad parameter.
    assert "Request does not contain valid json" in result.output


@failing_api_mock
def test_subscriptions_cancel_failure(invoke):
    """Cancel command exits gracefully from an API error."""
    result = invoke(
        ['cancel', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@cancel_mock
def test_subscriptions_cancel_success(invoke):
    """Cancel command succeeds."""
    result = invoke(
        ['cancel', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.


@failing_api_mock
def test_subscriptions_update_failure(invoke):
    """Update command exits gracefully from an API error."""
    result = invoke(
        ['update', 'test', json.dumps(GOOD_SUB_REQUEST)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@update_mock
def test_subscriptions_update_success(invoke):
    """Update command succeeds."""
    request = GOOD_SUB_REQUEST.copy()
    request['name'] = 'new_name'

    result = invoke(
        ['update', 'test', json.dumps(request)],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['name'] == 'new_name'


@failing_api_mock
def test_subscriptions_describe_failure(invoke):
    """Describe command exits gracefully from an API error."""
    result = invoke(
        ['describe', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@describe_mock
def test_subscriptions_describe_success(invoke):
    """Describe command succeeds."""
    result = invoke(
        ['describe', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert json.loads(result.output)['id'] == '42'


@failing_api_mock
def test_subscriptions_results_failure(invoke):
    """Results command exits gracefully from an API error."""
    result = invoke(
        ['results', 'test'],
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 1  # failure.


@pytest.mark.parametrize('options,expected_count',
                         [(['--status=created'], 100), ([], 100),
                          (['--limit=1', '--status=created'], 1),
                          (['--limit=2', '--pretty', '--status=created'], 2),
                          (['--limit=1', '--status=queued'], 0)])
@res_api_mock
# Remember, parameters come before fixtures in the function definition.
def test_subscriptions_results_success(invoke, options, expected_count):
    """Describe command succeeds."""
    result = invoke(
        ['results', 'test'] + options,
        # Note: catch_exceptions=True (the default) is required if we want
        # to exercise the "translate_exceptions" decorator and test for
        # failure.
        catch_exceptions=True)

    assert result.exit_code == 0  # success.
    assert result.output.count('"id"') == expected_count
