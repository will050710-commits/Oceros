"""Generate review evidence from actual subprocesses; never edit prior evidence.

Run from repo root: python task004/tools/validate_hardening.py --output <new-directory>
Requires authorized loopback sockets. Copies baseline/mutant into temporary directories,
never mutates the working source and never makes Git worktrees.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

import psutil

BASELINE = '2cb916803cef6c2c52f03107fddeb866c407ae27'
REVIEW_BASELINE = '07eb03cd0f01d16feef6f090cd5ed74c4c075eeb'
ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    'A1': ['task004.tests.test_hardening_server.ServerHardeningTests.test_a1_killed_cli_leaves_no_mock_or_owned_scratch'],
    'A2': ['task004.tests.test_hardening_record.AtomicArtifactTests.test_second_write_failure_cleans_staging_for_baseexceptions'],
    'A3': ['task004.tests.test_hardening_schema.ConfigBoundsTests'],
    'A4': ['task004.tests.test_hardening_schema.SchemaContractTests.test_a4_config_and_manifest_numerical_boundaries_match',
           'task004.tests.test_hardening_schema.SchemaContractTests.test_a4_reason_enum_matches_status_reasons',
           'task004.tests.test_hardening_schema.SchemaContractTests.test_a4_validate_artifact_checks_schema_before_value'],
    'A5': ['task004.tests.test_workflow.WorkflowTests.test_nonloopback_endpoint_rejected_before_connection'],
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def fingerprints():
    files = list((ROOT/'task004').glob('*.py'))
    for sub, pattern in [('tests', '*.py'), ('schemas', '*.json'), ('tools', '*.py')]:
        files.extend((ROOT/'task004'/sub).glob(pattern))
    files.extend((ROOT/'task004/references').rglob('*'))
    files.extend(ROOT/'task004'/name for name in ('mock_config.json', 'requirements.txt', 'setup.sh'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_file()}


def verification_scope():
    return f"{platform.system()}-executed mock tests; readiness requires result review"


def normalize_paths(text, locations):
    # Retain diagnostics; redact only known local prefixes, including repr-escaped paths.
    for path, label in sorted(locations.items(), key=lambda item: len(str(item[0])), reverse=True):
        path = str(path)
        for spelling in (path.replace('\\', '\\\\'), path.replace('\\', '/'), path):
            text = text.replace(spelling, label)
    return text


def extract_archive(data, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            target = (destination/member.name).resolve()
            if not target.is_relative_to(destination) or member.issym() or member.islnk():
                raise ValueError('unexpected baseline archive member')
        tar.extractall(destination, filter='data')
    return destination


DEFECT_ASSERTIONS = {
    'test_a1_killed_cli_leaves_no_mock_or_owned_scratch': ('mock survived harness SIGKILL',),
    'test_second_write_failure_cleans_staging_for_baseexceptions': ('partial artifact survived injected failure',),
    'test_a3_timeout_and_sampling_upper_bounds': ('ConfigError not raised',),
    'test_a3_validate_config_rejects_extreme_values': ('2', 'self.assertEqual(result, 2)'),
    'test_a4_config_and_manifest_numerical_boundaries_match': ('accepts, expected)', 'AssertionError: True != False'),
    'test_a4_reason_enum_matches_status_reasons': ('self.assertEqual(set(actual), set().union(*STATUS_REASONS.values()))',),
    'test_a4_validate_artifact_checks_schema_before_value': ('ValueError not raised',),
    'test_nonloopback_endpoint_rejected_before_connection': ('NON_LOOPBACK_ENDPOINT',),
    'test_nested_signal_cannot_deadlock_handler': ('nested signal deadlocked cancellation handler',),
    'test_inherited_ignore_is_preserved': ('inherited ignored SIGHUP requested cancellation',),
}


def expected_defect_failures(text):
    blocks = re.findall(r'^FAIL: (.*?)(?=^={10,}|^Ran |\Z)', text, re.MULTILINE | re.DOTALL)
    if not blocks:
        return False
    for block in blocks:
        method = block.split()[0]
        if method not in DEFECT_ASSERTIONS or 'AssertionError:' not in block:
            return False
        if not all(fragment in block for fragment in DEFECT_ASSERTIONS[method]):
            return False
    return True


def log_diagnostics(text, allow_expected_traceback=False):
    markers = ('Exception ignored', 'ResourceWarning') if allow_expected_traceback else ('Exception ignored', 'ResourceWarning', 'Traceback')
    return [marker for marker in markers if marker in text]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    summary = {'baseline_revision': BASELINE, 'review_baseline_revision': REVIEW_BASELINE, 'started_at_utc': utc(),
               'python': platform.python_version(), 'psutil': psutil.__version__,
               'platform': platform.system(), 'verification_scope': verification_scope(),
               'log_policy': 'Known local path prefixes normalized; diagnostic text preserved. Successful runs reject Exception ignored, ResourceWarning and Traceback.',
               'source_sha256': fingerprints(), 'runs': [], 'windows': 'UNVERIFIED', 'model': 'NOT_RUN'}
    failures = []
    locations = {ROOT: '<checkout>', Path(sys.prefix): '<python-env>', Path(sys.base_prefix): '<python-base>', Path.home(): '<home>', Path(tempfile.gettempdir()): '<temp>'}
    child_env = dict(os.environ, PYTHONWARNINGS='error::ResourceWarning')

    def run(label, cwd, args, expected_failure=False):
        command = [sys.executable, '-W', 'error::ResourceWarning', '-m', 'unittest', *args]
        start = time.monotonic()
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, env=child_env)
        text = normalize_paths(result.stdout.decode('utf-8', errors='replace'), locations)
        (output/f'{label}.log').write_text(text)
        count = re.search(r'Ran (\d+) tests? in ([0-9.]+)s', text)
        entry = {'label': label, 'command': ['<python>', *command[1:]], 'cwd': normalize_paths(str(cwd), locations), 'returncode': result.returncode,
                 'elapsed_s': time.monotonic()-start, 'tests_run': int(count[1]) if count else None,
                 'failures': int(re.search(r'failures=(\d+)', text)[1]) if re.search(r'failures=(\d+)', text) else 0,
                 'errors': int(re.search(r'errors=(\d+)', text)[1]) if re.search(r'errors=(\d+)', text) else 0,
                 'skipped': int(re.search(r'skipped=(\d+)', text)[1]) if re.search(r'skipped=(\d+)', text) else 0,
                 'expected_failure': expected_failure, 'log': f'{label}.log'}
        # Baseline/mutation evidence must be assertion failures, not missing imports.
        entry['diagnostic_markers'] = log_diagnostics(text, allow_expected_traceback=expected_failure)
        entry['defect_assertions_match'] = expected_defect_failures(text) if expected_failure else None
        ok = (entry['tests_run'] and entry['skipped'] == 0 and entry['errors'] == 0 and not entry['diagnostic_markers']
              and ((result.returncode != 0 and entry['failures'] > 0 and entry['defect_assertions_match']) if expected_failure else result.returncode == 0))
        entry['expectation_met'] = bool(ok)
        summary['runs'].append(entry)
        if not ok:
            failures.append(label)
        print(label, 'expected result' if ok else 'UNEXPECTED', 'tests=', entry['tests_run'], flush=True)

    try:
        with tempfile.TemporaryDirectory(prefix='task004-regression-') as tmp:
            temp_root = Path(tmp).resolve()
            baseline = temp_root/'baseline'
            locations[baseline] = '<baseline>'
            archive = subprocess.check_output(['git', 'archive', BASELINE], cwd=ROOT)
            extract_archive(archive, baseline)
            for name in ['test_hardening_server.py', 'test_hardening_record.py', 'test_hardening_schema.py', 'test_workflow.py', 'fixtures.py']:
                shutil.copy2(ROOT/'task004/tests'/name, baseline/'task004/tests'/name)
            for requirement, targets in TARGETS.items():
                # A5 hardens a TEST; the production guard already exists at baseline.
                # Its defect is demonstrated by the baseline test accepting a mutant.
                run(f'baseline-{requirement}', baseline, ['-v', *targets], expected_failure=requirement != 'A5')
                run(f'fixed-{requirement}', ROOT, ['-v', *targets])
            review = temp_root/'review-baseline'
            locations[review] = '<review-baseline>'
            extract_archive(subprocess.check_output(['git', 'archive', REVIEW_BASELINE], cwd=ROOT), review)
            shutil.copy2(ROOT/'task004/tests/test_review_cli.py', review/'task004/tests/test_review_cli.py')
            for name in ('test_nested_signal_cannot_deadlock_handler', 'test_inherited_ignore_is_preserved'):
                target = 'task004.tests.test_review_cli.ReviewCliTests.' + name
                run('review-baseline-' + name, review, ['-v', target], expected_failure=True)
                run('fixed-review-' + name, ROOT, ['-v', target])
            mutant = temp_root/'mutant'
            locations[mutant] = '<mutant>'
            shutil.copytree(ROOT/'task004', mutant/'task004', ignore=shutil.ignore_patterns('__pycache__', 'runs', 'hardening-*'))
            path = mutant/'task004/client.py'
            source = path.read_text()
            function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'request_synthetic')
            guard = next(node for node in function.body if isinstance(node, ast.If) and 'parsed.scheme' in ast.get_source_segment(source, node))
            lines = source.splitlines(keepends=True)
            removed = ''.join(lines[guard.lineno-1:guard.end_lineno])
            del lines[guard.lineno-1:guard.end_lineno]
            path.write_text(''.join(lines))
            (output/'mutation-A5-removed-guard.txt').write_text(removed)
            run('mutation-A5', mutant, ['-v', *TARGETS['A5']], expected_failure=True)
            baseline_client = baseline/'task004/client.py'
            old_source = baseline_client.read_text()
            old_function = next(n for n in ast.parse(old_source).body if isinstance(n, ast.FunctionDef) and n.name == 'request_synthetic')
            old_guard = next(n for n in old_function.body if isinstance(n, ast.If) and 'parsed.scheme' in ast.get_source_segment(old_source, n))
            old_lines = old_source.splitlines(keepends=True)
            del old_lines[old_guard.lineno-1:old_guard.end_lineno]
            baseline_client.write_text(''.join(old_lines))
            old_test = subprocess.check_output(['git', 'show', BASELINE + ':task004/tests/test_workflow.py'], cwd=ROOT)
            (baseline/'task004/tests/test_workflow.py').write_bytes(old_test)
            run('baseline-mutant-A5-undetected', baseline, ['-v', *TARGETS['A5']])
        # Required consecutive full-suite runs, with no intervening code edits.
        for index in range(1, 4):
            run(f'suite-{index}', ROOT, ['discover', '-s', 'task004/tests', '-v'])
        dry_command = [sys.executable, '-m', 'task004.cli', 'dry-run', '--output-dir', str(output/'dry-run')]
        dry = subprocess.run(dry_command, cwd=ROOT, capture_output=True, text=True, timeout=30, env=child_env)
        (output/'dry-run.stdout.log').write_text(normalize_paths(dry.stdout, locations))
        (output/'dry-run.stderr.log').write_text(normalize_paths(dry.stderr, locations))
        summary['dry_run'] = {'command': ['<python>', *[normalize_paths(arg, locations) for arg in dry_command[1:]]], 'returncode': dry.returncode, 'result': json.loads(dry.stdout), 'diagnostic_markers': log_diagnostics(dry.stdout + dry.stderr)}
        if dry.returncode or summary['dry_run']['result']['status'] != 'PASS' or summary['dry_run']['diagnostic_markers']:
            failures.append('dry-run')
        if fingerprints() != summary['source_sha256']:
            failures.append('source_changed_during_validation')
    except BaseException:
        failures.append('runner_interrupted_or_failed')
        raise
    finally:
        summary['finished_at_utc'] = utc()
        summary['failed_expectations'] = failures
        summary['status'] = 'PASS' if not failures and 'dry_run' in summary else 'FAIL'
        (output/'validation.json').write_text(json.dumps(summary, indent=2)+'\n')
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
