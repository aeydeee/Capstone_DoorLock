// Cache JSON data to avoid repeated AJAX calls
let cityData, provinceData, regionData, barangayData;

function loadData(callback) {
    const cityUrl = "/static/js/address/ph-json/city.json";
    const provinceUrl = "/static/js/address/ph-json/province.json";
    const regionUrl = "/static/js/address/ph-json/region.json";
    const barangayUrl = "/static/js/address/ph-json/barangay.json";

    $.when(
        $.getJSON(cityUrl, function (data) {
            cityData = data;
        }),
        $.getJSON(provinceUrl, function (data) {
            provinceData = data;
        }),
        $.getJSON(regionUrl, function (data) {
            regionData = data;
        }),
        $.getJSON(barangayUrl, function (data) {
            barangayData = data;
        })
    ).then(function () {
        if (callback) callback();
    });
}

function get_province_name(province_code) {
    let province = provinceData.find(
        (item) => item.province_code === province_code
    );
    return province ? province.province_name : "";
}

function get_region_name(region_code) {
    let region = regionData.find((item) => item.region_code === region_code);
    return region ? region.region_name : "";
}

function initializeAddressSelectors(citySelectId, barangaySelectId, cityTextId, barangayTextId) {
    let citySelect = $('#' + citySelectId);
    let barangaySelect = $('#' + barangaySelectId);
    let cityTextInput = $('#' + cityTextId);
    let barangayTextInput = $('#' + barangayTextId);


    cityData.forEach((entry) => {
        let province_name = get_province_name(entry.province_code);
        let region_name = get_region_name(entry.region_desc);

        citySelect.append(
            $('<option></option>')
                .attr('value', entry.city_code)
                .text(`${entry.city_name}, ${province_name}, ${region_name}`)
                .data('province', province_name)
                .data('region', region_name)
        );
    });

    // Initialize Select2
    citySelect.select2();
    barangaySelect.select2();

    // On city change
    citySelect.on('change', function () {
        let city_code = $(this).val();
        let city_text = $(this).find("option:selected").text();

        cityTextInput.val(city_text);

        // Add a console log to check if the field is set correctly
        console.log(cityTextInput.attr('id'), 'set to', city_text);

        setTimeout(function () {
            if (cityTextInput.val() === '') {
                alert('Address field for ' + cityTextId + ' is not populated yet.');
            }
        }, 100);

        // Populate barangay select
        barangaySelect.empty();
        barangaySelect.append('<option selected="true" disabled>Select Barangay</option>');

        let filteredBarangays = barangayData.filter(function (value) {
            return value.city_code === city_code;
        });

        filteredBarangays.sort(function (a, b) {
            return a.brgy_name.localeCompare(b.brgy_name);
        });

        filteredBarangays.forEach((entry) => {
            barangaySelect.append(
                $("<option></option>")
                    .attr("value", entry.brgy_code)
                    .text(entry.brgy_name)
            );
        });
        barangaySelect.val(null).trigger('change'); // reset barangay select
    });

    // On barangay change
    barangaySelect.on('change', function () {
        let barangay_text = $(this).find("option:selected").text();
        barangayTextInput.val(barangay_text);

        // Add a console log to check if the field is set correctly
        console.log(barangayTextInput.attr('id'), 'set to', barangay_text);
    });
}


$(document).ready(function () {
    // Ensure all address fields are populated before form submission
    $('form').on('submit', function (event) {
        const requiredFields = [
            '#home_city_text',
            '#curr_city_text',
            '#mother_city_text',
            '#elem_school_city_text',
            '#junior_hs_school_city_text',
        ];

        let allFieldsPopulated = true;
        requiredFields.forEach(function (selector) {
            if (!$(selector).val() || $(selector).val() === '') {
                allFieldsPopulated = false;
            }
        });


    });

    loadData(function () {
        initializeAddressSelectors('home_city_select', 'home_barangay_select', 'home_city_text', 'home_barangay_text');
        initializeAddressSelectors('curr_city_select', 'curr_barangay_select', 'curr_city_text', 'curr_barangay_text');
        initializeAddressSelectors('mother_city_select', 'mother_barangay_select', 'mother_city_text', 'mother_barangay_text');
        initializeAddressSelectors('father_city_select', 'father_barangay_select', 'father_city_text', 'father_barangay_text');
        initializeAddressSelectors('guardian_city_select', 'guardian_barangay_select', 'guardian_city_text', 'guardian_barangay_text');
        initializeAddressSelectors('elem_school_city_select', 'elem_school_barangay_select', 'elem_school_city_text', 'elem_school_barangay_text');
        initializeAddressSelectors('junior_hs_school_city_select', 'junior_hs_school_barangay_select', 'junior_hs_school_city_text', 'junior_hs_school_barangay_text');
        initializeAddressSelectors('senior_hs_school_city_select', 'senior_hs_school_barangay_select', 'senior_hs_school_city_text', 'senior_hs_school_barangay_text');
        initializeAddressSelectors('tertiary_school_city_select', 'tertiary_school_barangay_select', 'tertiary_school_city_text', 'tertiary_school_barangay_text');
    });
});
