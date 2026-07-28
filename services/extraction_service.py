from services.extractors.factory import ExtractorFactory


class ExtractionService:


    def extract(self, file_path):

        extractor = ExtractorFactory.get_extractor(
            file_path
        )

        return extractor.extract(
            file_path
        )