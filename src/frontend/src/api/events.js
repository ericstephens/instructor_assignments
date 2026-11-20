import client from './client.js'

export const listEvents = (params = {}) => client.get('/events', { params }).then(r => r.data)
export const getEvent = (id) => client.get(`/events/${id}`).then(r => r.data)
export const createEvent = (data) => client.post('/events', data).then(r => r.data)
export const updateEvent = (id, data) => client.put(`/events/${id}`, data).then(r => r.data)
