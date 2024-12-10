IA:
    time.sleep(10)
    api = webuiapi.WebUIApi()

    # create API client with custom host, port
    api = webuiapi.WebUIApi(host='uncanny.taile7da6.ts.net', port=7860, sampler = "Euler a")

    print(api.get_options()['sd_model_checkpoint'])