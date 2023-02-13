import logging
import os
import json
import textractmanifest as tm


def test_manifest_load(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/simple_feature_manifest.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore
        assert manifest
        assert manifest.s3_path


def test_classification_manifest_load(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_with_classification.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert manifest.classification == "EMPLOYMENT_APPLICATION"


def test_all_features(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_all_features.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert manifest.classification == "EMPLOYMENT_APPLICATION"


def test_manifest_queries_no_pages(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_queries_no_pages.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert manifest.queries_config


def test_manifest_queries_no_alias(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_queries_no_alias.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert manifest.queries_config


def test_manifest_queries_forms(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/queries_forms.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert manifest.queries_config


def test_manifest_creation_with_queries(caplog):
    manifest: tm.IDPManifest = tm.IDPManifest()
    manifest.s3_path = f"s3://somebucket/somekey"
    manifest.textract_features = ["QUERIES"]
    manifest.queries_config = list()
    manifest.queries_config.append(
        tm.Query(text="What is the Pay Period Start Date?",
                 alias='PAYSTUB_PAY_PERIOD_START_DATE'))
    manifest.queries_config.append(
        tm.Query(text="What is the Pay Period End Date?",
                 alias='PAYSTUB_PAY_PERIOD_END'))
    manifest.queries_config.append(
        tm.Query(text="What is the Pay Date?", alias='PAYSTUB_PAY_DATE'))
    manifest.queries_config.append(
        tm.Query(text="What is the Employee Name?",
                 alias='PAYSTUB_EMPLOYEE_NAME'))
    manifest.queries_config.append(
        tm.Query(text="What is the Employee Address?",
                 alias='PAYSTUB_EMPLOYEE_ADDRESS'))
    manifest.queries_config.append(
        tm.Query(text="What is the company Name?",
                 alias='PAYSTUB_COMPANY_NAME'))
    manifest.queries_config.append(
        tm.Query(text="What is the Current Gross Pay?",
                 alias='PAYSTUB_CURRENT_GROSS'))
    manifest.queries_config.append(
        tm.Query(text="What is the YTD Gross Pay?", alias='PAYSTUB_YTD_GROSS'))
    manifest.queries_config.append(
        tm.Query(text="What is the regular hourly rate?",
                 alias='PAYSTUB_REGULAR_HOURLY_RATE'))
    manifest.queries_config.append(
        tm.Query(text="What is the holiday rate?",
                 alias='PAYSTUB_HOLIDAY_RATE'))


def test_classification_manifest_metadata_load(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(
        p, "data/manifest_with_classification_and_metadata.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore
        assert manifest
        assert manifest.s3_path
        assert manifest.classification == "EMPLOYMENT_APPLICATION"
        assert manifest.meta_data[0].key
        assert manifest.meta_data[0].value


def test_manifest_minimal(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_minimal.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.s3_path
        assert not manifest.queries_config
        assert not manifest.textract_features


def test_manifest_analyze_id(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/analyze_id.json")
    with open(manifest_path) as f:
        j = json.load(f)
        assert j
        manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            j)  #type: ignore

        assert manifest
        assert manifest.document_pages
        assert len(manifest.document_pages) == 2
        assert not manifest.queries_config
        assert not manifest.textract_features


def test_manifest_merge(caplog):
    caplog.set_level(logging.DEBUG)
    p = os.path.dirname(os.path.realpath(__file__))
    manifest_path = os.path.join(p, "data/manifest_minimal.json")
    default_manifest_path = os.path.join(p, "data/manifest_default.json")
    with open(default_manifest_path) as f:
        default_manifest_json = json.load(f)
        assert default_manifest_json
        default_manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
            default_manifest_json)  #type: ignore
        with open(manifest_path) as g:
            manifest_json = json.load(g)
            assert manifest_json
            manifest: tm.IDPManifest = tm.IDPManifestSchema().load(
                manifest_json)  #type: ignore
            manifest.merge(default_manifest)
            assert manifest.s3_path == "s3://amazon-textract-public-content/blogs/employeeapp20210510.png"
            assert len(manifest.textract_features) == 1
            assert manifest.textract_features[0] == 'QUERIES'
            manifest.textract_features = ['FORMS', 'QUERIES']
            manifest.merge(default_manifest)
            assert not manifest.textract_features[0] == 'QUERIES'
