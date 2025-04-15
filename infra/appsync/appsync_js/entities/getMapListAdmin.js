/**
 * AppSync JS resolver for getMapListAdmin
 * This scans all entities and returns metadata, location, visibility, and request placeholders
 */

export function request(ctx) {
    return {
        operation: 'Scan'
    };
}
  
export function response(ctx) {
    const items = ctx.result.items || [];
  
    // Transform raw entity data into MapListEntity format
    const mapList = items.map((e) => ({
        id: e.id,
        role: e.role,
        name: e.name,
        logoObjectKey: e.logoObjectKey,
        dateFounded: e.dateFounded,
        industries: e.industries,
        description: e.description,
        location: {
            address: e?.location?.address,
            latlng: {
                lat: e?.location?.latlng?.lat,
                lng: e?.location?.latlng?.lng,
            },
        },
        nameChangeRequestStatus: {
            isApproved: null, // Placeholder until KAN-55 is integrated
        },
        visibility: e.visibility !== undefined ? Boolean(e.visibility) : true,
    }));
  
    // Count how many are startups and enablers
    const startupLength = mapList.filter((e) => e.role === 'startup').length;
    const enablersLength = mapList.filter((e) => e.role === 'enabler').length;
  
    // Placeholder for future name change request logic
    const requestList = []; // You will fetch and populate this in KAN-55
  
    return {
        mapList,
        requestList,
        startupLength,
        enablersLength,
        pendingRequestsLen: 0 // This will reflect the real pending requests count in the future
    };
}
  