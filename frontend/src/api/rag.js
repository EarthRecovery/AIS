import request from '@/utils/request'

export function ragAddContext(context, channel) {
    return request.post('/rag/add_context', {
        context,
        channel
    })
}

export function ragServiceAvailable() {
    return request.get('/rag/is_service_available')
}