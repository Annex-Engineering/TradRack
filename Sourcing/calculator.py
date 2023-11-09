import math

def main():
    lane_spacing = 17.
    c_cart_width = 28.9
    h_cart_width = 39.9
    extrusion_extra_len = 30.
    belt_base_len = 199.1
    belt_safety = 30.
    chain_pitch = 15
    chain_base_len = 120
    m3x8_base_count = 20
    m3x8_safety = 10
    m3x8_rail_pitch = 40.
    m3x8_rail_end = 4.5

    # get lane count
    lane_count = int(input("Enter the number of lanes: "))

    # calculate lane_span and minimum rail lengths
    lane_span = get_lane_span(lane_count, lane_spacing)
    c_rail_len = lane_span + c_cart_width
    h_rail_len = lane_span + h_cart_width

    # display required rail lengths
    print("\nMinimum rail length with c-cart: {}".format(c_rail_len))
    print("Minimum rail length with h-cart: {}".format(h_rail_len))

    # get rail cart type and corresponding minimum rail length
    cart_type = input("\nEnter selected rail cart type (c/h): ").lower()
    min_rail_len = c_rail_len if cart_type == "c" else h_rail_len

    # get rail length
    rail_len_str = input("Enter selected rail length "
                        "(leave blank to use minimum value): ")
    rail_len = max(float(rail_len_str), min_rail_len) if rail_len_str \
        else min_rail_len

    # check if user wants to increase the number of lanes
    cart_width = c_cart_width if cart_type == "c" else h_cart_width
    max_lane_count = math.floor((rail_len - cart_width) / lane_spacing) + 1
    if max_lane_count > lane_count:
        change_lane_count = input("Your selected rail allows a maximum of {} "
                                  "lanes. Increase lane count from {} to {}? "
                                  "(y/n): ".format(max_lane_count, lane_count, 
                                                   max_lane_count)).lower()
        if change_lane_count == "y":
            lane_count = max_lane_count
            lane_span = get_lane_span(lane_count, lane_spacing)

    print()

    # lane count
    print("Selected lane count: {}".format(lane_count))

    # rail
    print("Selected rail cart type: {}".format("c" if min_rail_len == c_rail_len \
        else "h"))
    print("Selected rail length: {}mm".format(rail_len))

    # extrusion
    extrusion_len = rail_len + extrusion_extra_len
    print("Minimum extrusion length: {}mm".format(extrusion_len))

    # belt
    belt_len = belt_base_len + lane_span * 2
    belt_len_rec = math.ceil(belt_len + belt_safety)
    print("Belt length: {}mm recommended ({}mm estimated)".format(belt_len_rec, 
                                                                belt_len))

    # cable chain
    chain_length = lane_span / 2 + chain_base_len
    chain_link_count = math.ceil(chain_length / chain_pitch)
    print("Approximate cable chain length: {}mm".format(chain_length))
    print("Quantity of cable chain links (not including the ends): {}" \
        .format(chain_link_count))

    # M3x8 screws and M3 T-nuts
    rail_screw_count = math.floor((rail_len - 2 * m3x8_rail_end) \
        / m3x8_rail_pitch) + 1
    m3x8_count = m3x8_base_count + lane_count + rail_screw_count
    m3x8_count_rec = m3x8_count + m3x8_safety
    t_nut_count = rail_screw_count + 1
    print("Quantity of M3 x 8mm Socket Head Cap Screws: {} recommended "
        "({} expected)".format(m3x8_count_rec, m3x8_count))
    print("Quantity of M3 Ball Spring T-Nuts: {}".format(t_nut_count))

def get_lane_span(lane_count, lane_spacing):
    return (lane_count - 1) * lane_spacing

if __name__ == "__main__":
    main()
