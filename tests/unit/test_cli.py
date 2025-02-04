import datetime
import io
from unittest.mock import create_autospec, patch

import pytest
import yaml

from databricks.labs.blueprint.tui import MockPrompts
from databricks.labs.remorph import cli
from databricks.labs.remorph.config import MorphConfig
from databricks.labs.remorph.helpers.recon_config_utils import ReconConfigPrompts
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound


@pytest.fixture
def mock_workspace_client_cli():
    state = {
        "/Users/foo/.remorph/config.yml": yaml.dump(
            {
                'version': 1,
                'catalog_name': 'transpiler',
                'schema_name': 'remorph',
                'source': 'snowflake',
                'sdk_config': {'cluster_id': 'test_cluster'},
            }
        )
    }

    def download(path: str) -> io.StringIO | io.BytesIO:
        if path not in state:
            raise NotFound(path)
        if ".csv" in path:
            return io.BytesIO(state[path].encode('utf-8'))
        return io.StringIO(state[path])

    workspace_client = create_autospec(WorkspaceClient)
    workspace_client.current_user.me().user_name = "foo"
    workspace_client.workspace.download = download
    return workspace_client


@pytest.fixture
def temp_dirs_for_lineage(tmpdir):
    input_dir = tmpdir.mkdir("input")
    output_dir = tmpdir.mkdir("output")

    sample_sql_file = input_dir.join("sample.sql")
    sample_sql_content = """
    create table table1 select * from table2 inner join
    table3 on table2.id = table3.id where table2.id in (select id from table4);
    create table table2 select * from table4;
    create table table5 select * from table3 join table4 on table3.id = table4.id;
    """
    sample_sql_file.write(sample_sql_content)

    return input_dir, output_dir


def test_transpile_with_invalid_dialect(mock_workspace_client_cli):
    with pytest.raises(Exception, match="Error: Invalid value for '--source'"):
        cli.transpile(
            mock_workspace_client_cli,
            "invalid_dialect",
            "/path/to/sql/file.sql",
            "/path/to/output",
            "true",
            "my_catalog",
            "my_schema",
            "current",
        )


def test_transpile_with_invalid_skip_validation(mock_workspace_client_cli):
    with (
        patch("os.path.exists", return_value=True),
        pytest.raises(Exception, match="Error: Invalid value for '--skip_validation'"),
    ):
        cli.transpile(
            mock_workspace_client_cli,
            "snowflake",
            "/path/to/sql/file.sql",
            "/path/to/output",
            "invalid_value",
            "my_catalog",
            "my_schema",
            "current",
        )


def test_invalid_input_sql(mock_workspace_client_cli):
    with (
        patch("os.path.exists", return_value=False),
        pytest.raises(Exception, match="Error: Invalid value for '--input_sql'"),
    ):
        cli.transpile(
            mock_workspace_client_cli,
            "snowflake",
            "/path/to/invalid/sql/file.sql",
            "/path/to/output",
            "true",
            "my_catalog",
            "my_schema",
            "current",
        )


def test_transpile_with_valid_input(mock_workspace_client_cli):
    source = "snowflake"
    input_sql = "/path/to/sql/file.sql"
    output_folder = "/path/to/output"
    skip_validation = "true"
    catalog_name = "my_catalog"
    schema_name = "my_schema"
    mode = "current"
    sdk_config = {'cluster_id': 'test_cluster'}

    with (
        patch("os.path.exists", return_value=True),
        patch("databricks.labs.remorph.cli.morph", return_value={}) as mock_morph,
    ):
        cli.transpile(
            mock_workspace_client_cli,
            source,
            input_sql,
            output_folder,
            skip_validation,
            catalog_name,
            schema_name,
            mode,
        )
        mock_morph.assert_called_once_with(
            mock_workspace_client_cli,
            MorphConfig(
                sdk_config=sdk_config,
                source=source,
                input_sql=input_sql,
                output_folder=output_folder,
                skip_validation=True,
                catalog_name=catalog_name,
                schema_name=schema_name,
                mode=mode,
            ),
        )


def test_transpile_empty_output_folder(mock_workspace_client_cli):
    source = "snowflake"
    input_sql = "/path/to/sql/file2.sql"
    output_folder = ""
    skip_validation = "false"
    catalog_name = "my_catalog"
    schema_name = "my_schema"

    mode = "current"
    sdk_config = {'cluster_id': 'test_cluster'}

    with (
        patch("os.path.exists", return_value=True),
        patch("databricks.labs.remorph.cli.morph", return_value={}) as mock_morph,
    ):
        cli.transpile(
            mock_workspace_client_cli,
            source,
            input_sql,
            output_folder,
            skip_validation,
            catalog_name,
            schema_name,
            mode,
        )
        mock_morph.assert_called_once_with(
            mock_workspace_client_cli,
            MorphConfig(
                sdk_config=sdk_config,
                source=source,
                input_sql=input_sql,
                output_folder=None,
                skip_validation=False,
                catalog_name=catalog_name,
                schema_name=schema_name,
                mode=mode,
            ),
        )


def test_transpile_with_incorrect_input_mode(mock_workspace_client_cli):

    with (
        patch("os.path.exists", return_value=True),
        pytest.raises(Exception, match="Error: Invalid value for '--mode':"),
    ):
        source = "snowflake"
        input_sql = "/path/to/sql/file2.sql"
        output_folder = ""
        skip_validation = "false"
        catalog_name = "my_catalog"
        schema_name = "my_schema"
        mode = "preview"

        cli.transpile(
            mock_workspace_client_cli,
            source,
            input_sql,
            output_folder,
            skip_validation,
            catalog_name,
            schema_name,
            mode,
        )


def test_transpile_with_incorrect_input_source(mock_workspace_client_cli):

    with (
        patch("os.path.exists", return_value=True),
        pytest.raises(Exception, match="Error: Invalid value for '--source':"),
    ):
        source = "postgres"
        input_sql = "/path/to/sql/file2.sql"
        output_folder = ""
        skip_validation = "false"
        catalog_name = "my_catalog"
        schema_name = "my_schema"
        mode = "preview"

        cli.transpile(
            mock_workspace_client_cli,
            source,
            input_sql,
            output_folder,
            skip_validation,
            catalog_name,
            schema_name,
            mode,
        )


def test_recon_with_invalid_recon_conf(mock_workspace_client_cli, tmp_path):
    with pytest.raises(Exception, match="Error: Invalid value for '--recon_conf'"):
        invalid_recon_conf_path = tmp_path / "invalid_recon_conf"
        valid_conn_profile_path = tmp_path / "valid_conn_profile"
        valid_conn_profile_path.touch()
        source = "snowflake"
        report = "data"
        cli.reconcile(
            mock_workspace_client_cli,
            str(invalid_recon_conf_path.absolute()),
            str(valid_conn_profile_path.absolute()),
            source,
            report,
        )


def test_recon_with_invalid_conn_profile(mock_workspace_client_cli, tmp_path):
    with pytest.raises(Exception, match="Error: Invalid value for '--conn_profile'"):
        valid_recon_conf_path = tmp_path / "valid_recon_conf"
        valid_recon_conf_path.touch()
        invalid_conn_profile_path = tmp_path / "invalid_conn_profile"
        source = "snowflake"
        report = "data"
        cli.reconcile(
            mock_workspace_client_cli,
            str(valid_recon_conf_path.absolute()),
            str(invalid_conn_profile_path.absolute()),
            source,
            report,
        )


def test_recon_with_invalid_source(mock_workspace_client_cli):
    recon_conf = "/path/to/recon/conf"
    conn_profile = "/path/to/conn/profile"
    source = "invalid_source"
    report = "data"

    with (
        patch("os.path.exists", return_value=True),
        pytest.raises(Exception, match="Error: Invalid value for '--source'"),
    ):
        cli.reconcile(mock_workspace_client_cli, recon_conf, conn_profile, source, report)


def test_recon_with_invalid_report(mock_workspace_client_cli):
    recon_conf = "/path/to/recon/conf"
    conn_profile = "/path/to/conn/profile"
    source = "snowflake"
    report = "invalid_report"

    with (
        patch("os.path.exists", return_value=True),
        pytest.raises(Exception, match="Error: Invalid value for '--report'"),
    ):
        cli.reconcile(mock_workspace_client_cli, recon_conf, conn_profile, source, report)


def test_recon_with_valid_input(mock_workspace_client_cli):
    recon_conf = "/path/to/recon/conf"
    conn_profile = "/path/to/conn/profile"
    source = "snowflake"
    report = "data"

    with patch("os.path.exists", return_value=True), patch("databricks.labs.remorph.cli.recon") as mock_recon:
        cli.reconcile(mock_workspace_client_cli, recon_conf, conn_profile, source, report)
        mock_recon.assert_called_once_with(recon_conf, conn_profile, source, report)


def test_generate_lineage_valid_input(temp_dirs_for_lineage, mock_workspace_client_cli):
    input_dir, output_dir = temp_dirs_for_lineage
    cli.generate_lineage(
        mock_workspace_client_cli, source="snowflake", input_sql=str(input_dir), output_folder=str(output_dir)
    )

    date_str = datetime.datetime.now().strftime("%d%m%y")
    output_filename = f"lineage_{date_str}.dot"
    output_file = output_dir.join(output_filename)
    assert output_file.check(file=1)
    expected_output = """
    flowchart TD
    Table1 --> Table2
    Table1 --> Table3
    Table1 --> Table4
    Table2 --> Table4
    Table3
    Table4
    Table5 --> Table3
    Table5 --> Table4
    """
    actual_output = output_file.read()
    assert actual_output.strip() == expected_output.strip()


def test_generate_lineage_with_invalid_dialect(mock_workspace_client_cli):
    with pytest.raises(Exception, match="Error: Invalid value for '--source'"):
        cli.generate_lineage(
            mock_workspace_client_cli,
            source="invalid_dialect",
            input_sql="/path/to/sql/file.sql",
            output_folder="/path/to/output",
        )


def test_generate_lineage_invalid_input_sql(mock_workspace_client_cli):
    with (
        patch("os.path.exists", return_value=False),
        pytest.raises(Exception, match="Error: Invalid value for '--input_sql'"),
    ):
        cli.generate_lineage(
            mock_workspace_client_cli,
            source="snowflake",
            input_sql="/path/to/invalid/sql/file.sql",
            output_folder="/path/to/output",
        )


def test_configure_secrets_databricks(mock_workspace_client):
    source_dict = {"databricks": "0", "netezza": "1", "oracle": "2", "snowflake": "3"}
    prompts = MockPrompts(
        {
            r"Select the source": source_dict["databricks"],
        }
    )

    recon_conf = ReconConfigPrompts(mock_workspace_client, prompts)
    recon_conf.prompt_source()

    recon_conf.prompt_and_save_connection_details()


def test_cli_configure_secrets_config(mock_workspace_client):
    with patch("databricks.labs.remorph.cli.ReconConfigPrompts") as mock_recon_config:
        cli.configure_secrets(mock_workspace_client)
        mock_recon_config.assert_called_once_with(mock_workspace_client)
