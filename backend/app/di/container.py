from dependency_injector import containers, providers
from app.config.settings import settings
from app.services.database.redis_service import RedisService
from app.services.database.postgres_service import PostgresService
from app.services.storage.s3_service import S3Service
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.services.modify_item_service import ModifyItemService
from app.services.category_service import CategoryService


class Container(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()
    
    # Database services
    redis_service = providers.Singleton(
        RedisService,
        redis_url=settings.redis_url
    )
    
    postgres_service = providers.Singleton(
        PostgresService,
        postgres_url=settings.postgres_url
    )
    
    # AWS services
    s3_service = providers.Singleton(
        S3Service,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        region=settings.aws_region,
        bucket=settings.s3_bucket
    )
    
    # Business services
    menu_service = providers.Singleton(MenuService)
    ingredient_service = providers.Singleton(IngredientService)
    category_service = providers.Singleton(CategoryService)
    modify_item_service = providers.Singleton(
        ModifyItemService,
        menu_service=menu_service,
        ingredient_service=ingredient_service
    )


# Global container instance
container = Container()
