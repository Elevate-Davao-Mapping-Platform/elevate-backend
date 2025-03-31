class CommonConstants:
    # DB Constants
    CLS = 'cls'
    HASH_KEY = 'hashKey'
    RANGE_KEY = 'rangeKey'

    LATEST_VERSION = 'latestVersion'
    ENTRY_STATUS = 'entryStatus'
    CREATE_DATE = 'createdAt'
    UPDATE_DATE = 'updateDate'
    CREATED_BY = 'createdBy'
    UPDATED_BY = 'updatedBy'

    ENTRY_ID = 'entryId'

    # Exclude to Comparison Keys
    EXCLUDE_COMPARISON_KEYS = [
        CLS,
        HASH_KEY,
        RANGE_KEY,
        ENTRY_STATUS,
        ENTRY_ID,
        CREATE_DATE,
        UPDATE_DATE,
        CREATED_BY,
        UPDATED_BY,
        LATEST_VERSION,
    ]
