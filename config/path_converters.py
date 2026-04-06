from django.core import signing


class SignedUIDConverter:
    regex = r"[^/]+"
    salt = "sigrh.uid"

    def to_python(self, value):
        if value.isdigit():
            return int(value)
        try:
            payload = signing.loads(value, salt=self.salt)
        except signing.BadSignature as exc:
            raise ValueError("Invalid signed UID") from exc
        try:
            return int(payload)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid UID payload") from exc

    def to_url(self, value):
        return signing.dumps(int(value), salt=self.salt)
