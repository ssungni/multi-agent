import random
import time
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import JWTError, jwt

class UserService:
    encoding: str = "UTF-8" 
    secret_key: str = "09049d379778597cfa341d7e91c7c2b7cb974924747548ca039c1e8af65771f5"
    jwt_algorithm: str = "HS256"

    def hash_password(self, plain_password: str) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt = bcrypt.gensalt()
        )
        return hashed_password.decode(self.encoding) #"UTF-8
    
    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.encoding), 
            hashed_password.encode(self.encoding)
        ) 

    def create_jwt(self, username: str) -> str:
        return jwt.encode(
            {
                "sub": username, # unique id
                "exp": datetime.now() + timedelta(days=1), # 토큰 만료 시간은 하루
            }, 
            self.secret_key, 
            algorithm=self.jwt_algorithm 
        )
    
    def decode_jwt(self, access_token: str) -> str:
        try:
            payload: dict = jwt.decode(
                access_token, self.secret_key, algorithms=[self.jwt_algorithm]
            )
        except JWTError:
            raise HTTPException(status_code=401, detail="Not Authorized")
        # expire
        return payload["sub"] # username

    @staticmethod
    def create_otp() -> int:
        return random.randint(1000, 9999)
    
    @staticmethod
    def send_email_to_user(email: str) -> None:
        time.sleep(10)
        print(f"Sending email to {email}!")
      