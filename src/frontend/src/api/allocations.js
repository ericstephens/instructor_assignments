import client from './client.js'

export const listAllocations = (params = {}) => client.get('/allocations', { params }).then(r => r.data)
export const createAllocation = (data) => client.post('/allocations', data).then(r => r.data)
export const deleteAllocation = (id) => client.delete(`/allocations/${id}`).then(r => r.data)
