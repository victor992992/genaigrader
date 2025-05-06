import math

def confidence_interval(data, confidence=0.95):
    n = len(data)
    if n < 1:
        raise ValueError("Need at least one data point")
    elif n ==1:
        return data[0], data[0], data[0]

    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    std_dev = math.sqrt(variance)
    std_err = std_dev / math.sqrt(n)

    # z-values for normal distribution
    z_values = {
        0.90: 1.6449,
        0.95: 1.9600,
        0.99: 2.5758,
    }

    # t-values for df = 1 to 29, for common confidence levels (two-tailed)
    t_values = {
        0.90: [6.314, 2.920, 2.353, 2.132, 2.015, 1.943, 1.895, 1.860, 1.833, 1.812,
               1.796, 1.782, 1.771, 1.761, 1.753, 1.746, 1.740, 1.734, 1.729, 1.725,
               1.721, 1.717, 1.714, 1.711, 1.708, 1.706, 1.703, 1.701, 1.699],
        0.95: [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
               2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
               2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045],
        0.99: [63.657, 9.925, 5.841, 4.604, 4.032, 3.707, 3.499, 3.355, 3.250, 3.169,
               3.106, 3.055, 3.012, 2.977, 2.947, 2.921, 2.898, 2.878, 2.861, 2.845,
               2.831, 2.819, 2.807, 2.797, 2.787, 2.779, 2.771, 2.763, 2.756],
    }

    if n < 30:
        t_list = t_values.get(confidence)
        if t_list is None:
            raise ValueError("Unsupported confidence level")
        t = t_list[n - 2]  # df = n - 1
    else:
        z = z_values.get(confidence)
        if z is None:
            raise ValueError("Unsupported confidence level")
        t = z

    margin = t * std_err
    return mean, mean - margin, mean + margin

def compute_averages(model_values, value_name):
    model_averages = []
    for model, data in model_values.items():
        values = data[value_name]
        n = len(values)
        if n < 1:
            continue

        avg, cinf, csup = confidence_interval(values, 0.95)
            
            # avg = sum(values) / n
            # variance = sum((x - avg)**2 for x in values) / (n - 1) if n > 1 else 0
            # std = math.sqrt(variance)
            # margin_error = 1.96 * (std / math.sqrt(n)) if n > 0 else 0 
            
        model_averages.append({
                'model__description': model,
                'avg': round(avg, 2),
                'yMin': round(cinf, 2),
                'yMax': round(csup, 2)
            })
        
    return model_averages, values