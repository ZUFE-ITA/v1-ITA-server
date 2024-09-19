export function objectIdToDate(id: string) {
    return new Date(parseInt(id.slice(0, 8), 16));
}