from os import access
from dns.dnssec import algorithm_from_text
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):   
    #model_config tell to load setting directly from env file          
    model_config= SettingsConfigDict(          
        env_file=".env",
        env_file_encoding="utf-8"
    )


    secret_key: SecretStr  # it is a private cryptographic string used to digitally sign and verify authentication tokens. Also SecretStr prevent key to show in log insted * is used
    algorithm: str = "HS256" # hashning algorithm
    access_token_expire_minutes: int = 30  #tokne expire in 30 minutes


settings= Settings()  # load everything from env file