import argparse
import json

from textractor import Textractor
from textractor.data.constants import (
    TextractAPI,
    TextractFeatures,
    CLIPrint,
    CLIOverlay,
)
from textractor.exceptions import InputError
from textractor.visualizers.entitylist import EntityList

STRING_DICT = {
    # Textractor parameters
    "PROFILE_NAME": "AWS profile name to use for the request",
    "REGION": "AWS region to use for the request",
    # Subcommand decriptions
    "DETECT_DOCUMENT_TEXT": "Synchronous API for Optical Character Recognition",
    "START_DOCUMENT_TEXT_DETECTION": "Asynchronous API for Optical Character Recognition",
    "ANALYZE_DOCUMENT": "Synchronous API for document analysis (forms, tables, queries, and signatures)",
    "START_DOCUMENT_ANALYSIS": "Asynchronous API for document analysis (forms, tables, queries, and signatures)",
    "ANALYZE_EXPENSE": "Synchronous API for expense analysis",
    "START_EXPENSE_ANALYSIS": "Asynchronous API for expense analysis",
    "ANALYZE_ID": "API for identity document analysis (supports driver's license and passports).",
    "GET_RESULT": "Try to fetch the result for a given job id",
    # Parameter descriptions
    "OUTPUT_FILE": "Output file to save the response, can be an S3 path",
    "INPUT_FILE_SYNC": "File to process, must be of type JPEG, PNG, TIFF, BMP. Can be an S3 path",
    "INPUT_FILE_ASYNC": "File to process, must be of type PDF, JPEG, PNG, TIFF, BMP. The file has to be in S3, you you can provide an S3 path with --upload-s3-path",
    "GET_RESULT_JOB_ID": "Job ID, as returned by any of the asynchronous functions",
    "QUERIES": 'List of queries, use quotes (") to escape spaces',
    "S3_UPLOAD_PATH": "Path to upload the input files to, required if input_file is not an S3 path",
    "S3_OUTPUT_PATH": "Path to write the response to",
    "GET_RESULT_API": "API used to make the request",
    # Output print
    "PRINT": "Print the output in a readable format",
    # Overlay
    "OVERLAY": "Save an image of the document with the words, lines, form fields, and tables overlayed on top",
    "FONT_SIZE_RATIO": "Scales the text up or down, default is 0.75, which would be half the pixel height",
}

def _build_parser():
    parser = argparse.ArgumentParser(
        description="Commandline interface for the Textractor library"
    )

    subparsers = parser.add_subparsers(help="Sub-command help", dest="subcommand")

    # DocumentText parsers
    parser_detect_document_text = subparsers.add_parser(
        "detect-document-text", help=STRING_DICT["DETECT_DOCUMENT_TEXT"]
    )
    parser_detect_document_text.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_SYNC"]
    )
    parser_detect_document_text.add_argument(
        "output_file", type=str, help=STRING_DICT["OUTPUT_FILE"]
    )
    parser_detect_document_text.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_detect_document_text.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )
    parser_detect_document_text.add_argument(
        "--print",
        choices=[cd.name for cd in CLIPrint],
        nargs="+",
        help=STRING_DICT["PRINT"],
    )
    parser_detect_document_text.add_argument(
        "--overlay",
        choices=[cd.name for cd in CLIOverlay],
        nargs="+",
        help=STRING_DICT["OVERLAY"],
    )
    parser_detect_document_text.add_argument(
        "--font-size-ratio",
        type=float,
        help=STRING_DICT["FONT_SIZE_RATIO"],
        default=0.75,
    )

    parser_start_document_text_detection = subparsers.add_parser(
        "start-document-text-detection", help=STRING_DICT["START_DOCUMENT_TEXT_DETECTION"]
    )
    parser_start_document_text_detection.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_ASYNC"]
    )
    parser_start_document_text_detection.add_argument(
        "--s3-upload-path", type=str, help=STRING_DICT["S3_UPLOAD_PATH"]
    )
    parser_start_document_text_detection.add_argument(
        "--s3-output-path", type=str, help=STRING_DICT["S3_OUTPUT_PATH"]
    )
    parser_start_document_text_detection.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_start_document_text_detection.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )

    # analyze-document parsers
    parser_analyze_document = subparsers.add_parser(
        "analyze-document", help=STRING_DICT["ANALYZE_DOCUMENT"]
    )
    parser_analyze_document.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_SYNC"]
    )
    parser_analyze_document.add_argument(
        "output_file", type=str, help=STRING_DICT["OUTPUT_FILE"]
    )
    parser_analyze_document.add_argument(
        "--features",
        choices=[tf.name for tf in TextractFeatures],
        nargs="+",
        required=True,
    )
    parser_analyze_document.add_argument(
        "--queries", type=str, nargs="+", help=STRING_DICT["QUERIES"]
    )
    parser_analyze_document.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_analyze_document.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )
    parser_analyze_document.add_argument(
        "--print",
        choices=[cd.name for cd in CLIPrint],
        nargs="+",
        help=STRING_DICT["PRINT"],
    )
    parser_analyze_document.add_argument(
        "--overlay",
        choices=[cd.name for cd in CLIOverlay],
        nargs="+",
        help=STRING_DICT["OVERLAY"],
    )
    parser_analyze_document.add_argument(
        "--font-size-ratio",
        type=float,
        help=STRING_DICT["FONT_SIZE_RATIO"],
        default=0.75,
    )

    parser_start_document_analysis = subparsers.add_parser(
        "start-document-analysis", help=STRING_DICT["START_DOCUMENT_ANALYSIS"]
    )
    parser_start_document_analysis.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_ASYNC"]
    )
    parser_start_document_analysis.add_argument(
        "--features",
        choices=[tf.name for tf in TextractFeatures],
        nargs="+",
        required=True,
    )
    parser_start_document_analysis.add_argument(
        "--queries", type=str, nargs="+", help=STRING_DICT["QUERIES"]
    )
    parser_start_document_analysis.add_argument(
        "--s3-upload-path", type=str, help=STRING_DICT["S3_UPLOAD_PATH"]
    )
    parser_start_document_analysis.add_argument(
        "--s3-output-path", type=str, help=STRING_DICT["S3_OUTPUT_PATH"]
    )
    parser_start_document_analysis.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_start_document_analysis.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )

    # analyze-expense parsers
    parser_analyze_expense = subparsers.add_parser(
        "analyze-expense", help=STRING_DICT["ANALYZE_EXPENSE"]
    )
    parser_analyze_expense.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_SYNC"]
    )
    parser_analyze_expense.add_argument(
        "output_file", type=str, help=STRING_DICT["OUTPUT_FILE"]
    )
    parser_analyze_expense.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_analyze_expense.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )
    parser_analyze_expense.add_argument(
        "--print",
        choices=[cd.name for cd in CLIPrint],
        nargs="+",
        help=STRING_DICT["PRINT"],
    )
    parser_analyze_expense.add_argument(
        "--overlay",
        choices=[cd.name for cd in CLIOverlay],
        nargs="+",
        help=STRING_DICT["OVERLAY"],
    )
    parser_analyze_expense.add_argument(
        "--font-size-ratio",
        type=float,
        help=STRING_DICT["FONT_SIZE_RATIO"],
        default=0.75,
    )

    parser_start_expense_analysis = subparsers.add_parser(
        "start-expense-analysis", help=STRING_DICT["START_EXPENSE_ANALYSIS"]
    )
    parser_start_expense_analysis.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_ASYNC"]
    )
    parser_start_expense_analysis.add_argument(
        "--s3-upload-path", type=str, help=STRING_DICT["S3_UPLOAD_PATH"]
    )
    parser_start_expense_analysis.add_argument(
        "--s3-output-path", type=str, help=STRING_DICT["S3_OUTPUT_PATH"]
    )
    parser_start_expense_analysis.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_start_expense_analysis.add_argument(
        "--region-name", type=str, help=STRING_DICT["REGION"]
    )

    # analyze-id parsers
    parser_analyze_id = subparsers.add_parser(
        "analyze-id", help=STRING_DICT["ANALYZE_ID"]
    )
    parser_analyze_id.add_argument(
        "file_source", type=str, help=STRING_DICT["INPUT_FILE_SYNC"]
    )
    parser_analyze_id.add_argument(
        "output_file", type=str, help=STRING_DICT["OUTPUT_FILE"]
    )
    parser_analyze_id.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_analyze_id.add_argument("--region-name", type=str, help=STRING_DICT["REGION"])
    parser_analyze_id.add_argument(
        "--print",
        choices=[cd.name for cd in CLIPrint],
        nargs="+",
        help=STRING_DICT["PRINT"],
    )

    # get-result parsers
    parser_get_result = subparsers.add_parser(
        "get-result", help=STRING_DICT["GET_RESULT"]
    )
    parser_get_result.add_argument(
        "job_id", type=str, help=STRING_DICT["GET_RESULT_JOB_ID"]
    )
    parser_get_result.add_argument(
        "api",
        type=str,
        choices=[ta.name for ta in TextractAPI],
        help=STRING_DICT["GET_RESULT_API"],
    )
    parser_get_result.add_argument(
        "output_file", type=str, help=STRING_DICT["OUTPUT_FILE"]
    )
    parser_get_result.add_argument(
        "--profile-name", type=str, help=STRING_DICT["PROFILE_NAME"]
    )
    parser_get_result.add_argument("--region-name", type=str, help=STRING_DICT["REGION"])
    parser_get_result.add_argument(
        "--print",
        choices=[cd.name for cd in CLIPrint],
        nargs="+",
        help=STRING_DICT["PRINT"],
    )
    return parser

def textractor_cli():
    """
    CLI for Textractor
    """

    parser = _build_parser()

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help()
        return

    if args.profile_name is None and args.region_name is None:
        args.profile_name = "default"

    extractor = Textractor(
        profile_name=args.profile_name,
        region_name=args.region_name,
    )

    s3_output_path = None
    if "output_file" in args and args.output_file.startswith("s3://"):
        s3_output_path = args.output_file

    # ASYNC is handled differently
    if args.subcommand.startswith("start"):
        if not args.file_source.startswith("s3://") and args.s3_upload_path is None:
            raise InputError(
                "--s3-upload-path is required if file_source is not an S3 path"
            )
        if args.subcommand == "start-document-text-detection":
            out = extractor.start_document_text_detection(
                args.file_source,
                s3_output_path=args.s3_output_path,
                s3_upload_path=args.s3_upload_path,
            )
        elif args.subcommand == "start-document-analysis":
            out = extractor.start_document_analysis(
                args.file_source,
                features=[TextractFeatures[feat] for feat in args.features],
                queries=args.queries,
                s3_output_path=args.s3_output_path,
                s3_upload_path=args.s3_upload_path,
            )
        elif args.subcommand == "start-expense-analysis":
            out = extractor.start_expense_analysis(
                args.file_source,
                s3_output_path=args.s3_output_path,
                s3_upload_path=args.s3_upload_path,
            )
        print(out.job_id)
    # SYNC
    else:
        if args.subcommand == "detect-document-text":
            out = extractor.detect_document_text(
                args.file_source,
                s3_output_path=s3_output_path,
            )
        elif args.subcommand == "analyze-document":
            out = extractor.analyze_document(
                args.file_source,
                features=[TextractFeatures[feat] for feat in args.features],
                queries=args.queries,
                s3_output_path=s3_output_path,
            )
        elif args.subcommand == "analyze-expense":
            out = extractor.analyze_expense(
                args.file_source,
                s3_output_path=s3_output_path,
            )
        elif args.subcommand == "analyze-id":
            out = extractor.analyze_id(
                args.file_source,
            )
        elif args.subcommand == "get-result":
            out = extractor.get_result(
                args.job_id,
                TextractAPI[args.api],
            )

        if args.print is not None:
            if "ALL" in args.print or "TEXT" in args.print:
                print(out.text)
            if "ALL" in args.print or "TABLES" in args.print:
                print(out.tables.pretty_print())
            if "ALL" in args.print or "FORMS" in args.print:
                print(out.key_values.pretty_print())
            if "ALL" in args.print or "QUERIES" in args.print:
                print(out.queries.pretty_print())
            if "ALL" in args.print or "EXPENSES" in args.print:
                print(out.expense_documents.pretty_print())
            if "ALL" in args.print or "SIGNATURES" in args.print:
                print(out.signatures.pretty_print())
            if "ALL" in args.print or "IDS" in args.print:
                print(out.identity_documents.pretty_print())

        if "overlay" in args and args.overlay is not None:
            entity_list = EntityList()
            if "ALL" in args.overlay or "WORDS" in args.overlay:
                entity_list += out.words
            if "ALL" in args.overlay or "LINES" in args.overlay:
                entity_list += out.lines
            if "ALL" in args.overlay or "TABLES" in args.overlay:
                entity_list += out.tables
            if "ALL" in args.overlay or "FORMS" in args.overlay:
                entity_list += out.key_values
            if "ALL" in args.overlay or "QUERIES" in args.overlay:
                entity_list += out.queries
            if "ALL" in args.overlay or "SIGNATURES" in args.overlay:
                entity_list += out.signatures
            image = entity_list.visualize(
                with_text=True,
                font_size_ratio=args.font_size_ratio,
            )
            image.save(f"{args.output_file}.png")

        with open(args.output_file, "w") as f:
            json.dump(out.response, f)


if __name__ == "__main__":
    textractor_cli()
