import client from './client.js'

export const listEventDates = (params = {}) => client.get('/event-dates', { params }).then(r => r.data)
export const getEventDate = (id) => client.get(`/event-dates/${id}`).then(r => r.data)
export const createEventDate = (data) => client.post('/event-dates', data).then(r => r.data)
export const getStaffingStatus = (id) => client.get(`/event-dates/${id}/staffing-status`).then(r => r.data)
export const cancelEventDate = (id) => client.post(`/event-dates/${id}/cancel`).then(r => r.data)
