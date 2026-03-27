# 게시판
from app.models.board import BoardPost, BoardAttachment

# SA-03. 데이터표준 (기존)
from app.models.standard import StdWord, StdDomain, StdTerm, StdCode, StdRequest, StdRequestHistory
from app.models.classification import DataClassification, DataGrade, ClassificationSyncLog
from app.models.meta_model import MetaModel, MetaModelEntity, MetaModelAttribute
from app.models.quality import QualityRule, QualityCheckResult, StdComplianceResult, QualitySchedule
from app.models.audit import StdAuditLog

# SA-01. 공통/시스템
from app.models.system import (
    SysConfig, SysInfrastructure, SysCloudConfig, SysDrBackup,
    SysPackage, SysInterface, SysIntegration, SysDmzLink,
)

# SA-02. 사용자/권한
from app.models.user import (
    UserAccount, UserRole, UserPermission, UserRolePermission,
    UserRoleMap, UserDataAccessPolicy, UserAccessRequest,
    UserLoginHistory, UserSession,
)

# SA-04. 데이터자산/카탈로그
from app.models.catalog import (
    CatalogDataset, CatalogColumn, CatalogTag, CatalogDatasetTag,
    CatalogLineage, CatalogSearchIndex,
)

# SA-05. 데이터수집
from app.models.collection import (
    CollectionStrategy, CollectionDataSource, CollectionDatasetConfig,
    CollectionSchedule, CollectionJob, CollectionMigration,
    CollectionExternalAgency, CollectionSpatialConfig,
)

# SA-06. 데이터정제
from app.models.cleansing import (
    CleansingRule, CleansingJob, CleansingResultDetail,
    AnonymizationConfig, AnonymizationLog,
    TransformModel, TransformMapping,
    CleansingJobRule,
)

# SA-07. 데이터저장
from app.models.storage import (
    StorageZone, StorageHighspeedDb, StorageUnstructured, StorageDatasetLocation,
)

# SA-08. 데이터유통
from app.models.distribution import (
    DistributionConfig, DistributionDataset, DistributionFormat,
    DistributionRequest, DistributionDownloadLog,
    DistributionApiEndpoint, DistributionApiKey, DistributionApiUsageLog,
    DistributionMcpConfig, DistributionFusionModel, DistributionStats,
    DistributionRequestDataset, DistributionFusionSource, DistributionApiKeyEndpoint,
)

# SA-09. 포털/UX
from app.models.portal import (
    PortalDashboardTemplate, PortalDashboardWidget, PortalUserDashboard,
    PortalVisualizationChart, PortalChartTemplate,
    PortalBookmark, PortalRecentView, PortalSearchHistory,
    PortalNotification, PortalNotificationSubscription, PortalSitemapMenu,
)

# SA-10. 운영/감사
from app.models.operation import (
    OperationHubStats, OperationReportTemplate, OperationReportGeneration,
    OperationAiQueryLog, OperationAiModelConfig,
    OperationAccessLog, OperationSystemEvent,
)

__all__ = [
    # SA-03 데이터표준 (기존 15 + 신규 2 = 17)
    "StdWord", "StdDomain", "StdTerm", "StdCode", "StdRequest", "StdRequestHistory",
    "DataClassification", "DataGrade", "ClassificationSyncLog",
    "MetaModel", "MetaModelEntity", "MetaModelAttribute",
    "QualityRule", "QualityCheckResult", "StdComplianceResult", "QualitySchedule",
    "StdAuditLog",
    # SA-01 공통/시스템 (8)
    "SysConfig", "SysInfrastructure", "SysCloudConfig", "SysDrBackup",
    "SysPackage", "SysInterface", "SysIntegration", "SysDmzLink",
    # SA-02 사용자/권한 (9)
    "UserAccount", "UserRole", "UserPermission", "UserRolePermission",
    "UserRoleMap", "UserDataAccessPolicy", "UserAccessRequest",
    "UserLoginHistory", "UserSession",
    # SA-04 데이터자산/카탈로그 (6)
    "CatalogDataset", "CatalogColumn", "CatalogTag", "CatalogDatasetTag",
    "CatalogLineage", "CatalogSearchIndex",
    # SA-05 데이터수집 (8)
    "CollectionStrategy", "CollectionDataSource", "CollectionDatasetConfig",
    "CollectionSchedule", "CollectionJob", "CollectionMigration",
    "CollectionExternalAgency", "CollectionSpatialConfig",
    # SA-06 데이터정제 (8)
    "CleansingRule", "CleansingJob", "CleansingResultDetail",
    "AnonymizationConfig", "AnonymizationLog",
    "TransformModel", "TransformMapping",
    "CleansingJobRule",
    # SA-07 데이터저장 (4)
    "StorageZone", "StorageHighspeedDb", "StorageUnstructured", "StorageDatasetLocation",
    # SA-08 데이터유통 (14)
    "DistributionConfig", "DistributionDataset", "DistributionFormat",
    "DistributionRequest", "DistributionDownloadLog",
    "DistributionApiEndpoint", "DistributionApiKey", "DistributionApiUsageLog",
    "DistributionMcpConfig", "DistributionFusionModel", "DistributionStats",
    "DistributionRequestDataset", "DistributionFusionSource", "DistributionApiKeyEndpoint",
    # SA-09 포털/UX (11)
    "PortalDashboardTemplate", "PortalDashboardWidget", "PortalUserDashboard",
    "PortalVisualizationChart", "PortalChartTemplate",
    "PortalBookmark", "PortalRecentView", "PortalSearchHistory",
    "PortalNotification", "PortalNotificationSubscription", "PortalSitemapMenu",
    # SA-10 운영/감사 (7)
    "OperationHubStats", "OperationReportTemplate", "OperationReportGeneration",
    "OperationAiQueryLog", "OperationAiModelConfig",
    "OperationAccessLog", "OperationSystemEvent",
]
