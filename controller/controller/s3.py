from sqlalchemy import Column, BigInteger, String

import meta

class S3(meta.Base):
    __tablename__ = 's3'

    s3id = Column(BigInteger, unique=True, nullable=False, \
                      autoincrement=True, primary_key=True)
    bucket = Column(String, unique=True, index=True)
    access_key = Column(String)
    secret = Column(String)
